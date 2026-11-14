import io
import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from server.domain import Session
from server.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    monkeypatch.delenv("FIRSTFIVE_ACCESS_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with TestClient(create_app(tmp_path)) as c:
        yield c


def until(ws, kind):
    for _ in range(40):
        data = ws.receive()
        if data.get("text"):
            value = json.loads(data["text"])
            if value.get("type") == kind:
                return value
    raise AssertionError("Expected " + kind)


def start(app):
    app.send_json({"type": "alert", "ts": -100000, "lat": 60.18, "lon": 24.83})
    return until(app, "state")["session_id"]


def answer(app, step, value="no"):
    app.send_json({"type": "answer", "step_id": step, "value": value})
    return until(app, "state")


def test_full_scenario_and_persistence(client):
    with (
        client.websocket_connect("/ws/app") as app,
        client.websocket_connect("/ws/ui?role=operator") as op,
    ):
        until(app, "state")
        until(op, "state")
        sid = start(app)
        assert answer(app, "responsive")["step"] == "breathing"
        assert answer(app, "breathing")["step"] == "cpr"
        op.send_json({"type": "pickup"})
        until(app, "pickup")
        assert until(app, "state")["phase"] == "connected"
        op.send_json({"type": "dispatcher_said", "text": "Keep pushing.", "final": True})
        assert until(app, "caller_heard")["text"] == "Keep pushing."
        op.send_json({"type": "end"})
        until(app, "end")
        until(op, "report_ready")
        record = client.get("/session/" + sid).json()
        assert record["phase"] == "ended" and record["report_status"] == "done"
        assert record["report"]["metrics"]["alert_to_cpr_guidance_seconds"] >= 0
        assert record["dialogue"][0]["text"] == "Keep pushing."
        assert record["report"]["handover"][0]["sources"]
        html = client.get("/report/" + sid).text
        assert "Keep pushing." in html and "No actual emergency" not in html
        assert (client.app.state.hub.directory / sid / "session.json").exists()


@pytest.mark.parametrize(
    "step,answers",
    [
        ("stay", [("responsive", "yes")]),
        ("stay", [("responsive", "no"), ("breathing", "yes")]),
    ],
)
def test_yes_branches_do_not_claim_cpr(client, step, answers):
    with client.websocket_connect("/ws/app") as app:
        until(app, "state")
        start(app)
        for s, a in answers:
            state = answer(app, s, a)
        assert state["step"] == step
        assert client.app.state.hub.session.cpr_at is None


def test_invalid_and_late_answers(client):
    with (
        client.websocket_connect("/ws/app") as app,
        client.websocket_connect("/ws/ui?role=operator") as op,
    ):
        until(app, "state")
        start(app)
        app.send_json({"type": "answer", "step_id": "breathing", "value": "no"})
        assert "active guide" in until(app, "error")["message"]
        op.send_json({"type": "pickup"})
        until(app, "pickup")
        app.send_json({"type": "answer", "step_id": "responsive", "value": "no"})
        assert until(app, "error")
        assert client.app.state.hub.session.answers == {}


def test_read_only_and_bad_payload(client):
    with client.websocket_connect("/ws/ui?role=viewer") as view:
        until(view, "state")
        view.send_json({"type": "override", "action": "trigger"})
        assert "role" in until(view, "error")["message"]
        view.send_text("[")
        assert until(view, "error")
        view.send_json([])
        assert until(view, "error")
        assert client.app.state.hub.session is None


def test_images_reconnect_reset(client):
    image = Image.new("RGB", (20, 20))
    b = io.BytesIO()
    image.save(b, format="JPEG")
    jpeg = b.getvalue()
    with (
        client.websocket_connect("/ws/app") as app,
        client.websocket_connect("/ws/ui?role=operator") as op,
    ):
        until(app, "state")
        sid = start(app)
        app.send_bytes(b"not a jpeg")
        assert until(app, "error")
        app.send_bytes(jpeg)
        # Barrier: next event cannot complete until frame has been handled.
        answer(app, "responsive")
        with client.websocket_connect("/ws/ui?role=viewer") as view:
            assert until(view, "state")["session_id"] == sid
            assert view.receive_bytes() == jpeg
        record = client.get("/session/" + sid).json()
        assert len(record["frames"]) == 2
        assert client.get(f"/session/{sid}/" + record["frames"][0]["file"]).content == jpeg
        op.send_json({"type": "override", "action": "reset"})
        until(app, "override")
        assert until(app, "state")["phase"] == "idle"
        assert client.get("/session/" + sid).json()["phase"] == "ended"


def test_upload_validation_and_fallback(client):
    with (
        client.websocket_connect("/ws/app") as app,
        client.websocket_connect("/ws/ui?role=operator") as op,
    ):
        until(app, "state")
        sid = start(app)
        assert (
            client.post(f"/session/{sid}/audio?track=caller", content=b"x" * 20).status_code == 409
        )
        op.send_json({"type": "pickup"})
        until(app, "pickup")
        until(app, "state")
        assert client.post(f"/session/{sid}/audio?track=bad", content=b"x" * 20).status_code == 400
        assert (
            client.post(
                f"/session/{sid}/audio?track=caller&offset=-1", content=b"x" * 20
            ).status_code
            == 400
        )
        r = client.post(
            f"/session/{sid}/audio?track=caller",
            content=b"x" * 20,
            headers={"Content-Type": "audio/webm"},
        )
        assert r.status_code == 200
        op.send_json({"type": "end"})
        until(op, "report_ready")
        record = client.get("/session/" + sid).json()
        assert any("transcription unavailable" in w for w in record["warnings"])
        assert record["dialogue"] == []
        assert (
            client.post(f"/session/{sid}/audio?track=caller", content=b"x" * 20).status_code == 409
        )


def test_report_escapes_untrusted_text(client):
    with (
        client.websocket_connect("/ws/app") as app,
        client.websocket_connect("/ws/ui?role=operator") as op,
    ):
        until(app, "state")
        sid = start(app)
        op.send_json({"type": "pickup"})
        until(app, "pickup")
        op.send_json(
            {
                "type": "dispatcher_said",
                "text": "<script>alert(1)</script>",
                "final": True,
            }
        )
        until(app, "caller_heard")
        op.send_json({"type": "end"})
        until(op, "report_ready")
        html = client.get("/report/" + sid).text
        assert "&lt;script&gt;" in html and "<script>alert" not in html


def test_key_auth_and_cross_origin(tmp_path, monkeypatch):
    monkeypatch.setenv("FIRSTFIVE_ACCESS_KEY", "demo-secret")
    with TestClient(create_app(tmp_path)) as c:
        assert c.get("/health").status_code == 401
        assert c.get("/health", headers={"X-FirstFive-Key": "demo-secret"}).status_code == 200
        from starlette.websockets import WebSocketDisconnect

        with pytest.raises(WebSocketDisconnect):
            with c.websocket_connect("/ws/ui?role=operator"):
                pass
        with pytest.raises(WebSocketDisconnect):
            with c.websocket_connect(
                "/ws/ui?role=operator?key=demo-secret",
                headers={"origin": "https://evil.example"},
            ):
                pass


def test_livekit_missing_and_room_scoping(client, monkeypatch):
    assert client.get("/livekit/token?role=bad").status_code == 400
    assert client.get("/livekit/token?role=caller").status_code == 409
    with (
        client.websocket_connect("/ws/app") as app,
        client.websocket_connect("/ws/ui?role=operator") as op,
    ):
        until(app, "state")
        sid = start(app)
        op.send_json({"type": "pickup"})
        until(app, "pickup")
        until(app, "state")
        monkeypatch.delenv("LIVEKIT_URL", raising=False)
        assert client.get("/livekit/token?role=caller").status_code == 503
        monkeypatch.setenv("LIVEKIT_URL", "wss://example.invalid")
        monkeypatch.setenv("LIVEKIT_API_KEY", "test")
        monkeypatch.setenv("LIVEKIT_API_SECRET", "a" * 32)
        token = client.get("/livekit/token?role=caller").json()["token"]
        import jwt

        payload = jwt.decode(token, "a" * 32, algorithms=["HS256"])
        assert payload["video"]["room"] == "firstfive-" + sid
        assert payload["sub"] == "caller" and payload["exp"] - payload["nbf"] == 1800


def test_reports_survive_new_app(client):
    with (
        client.websocket_connect("/ws/app") as app,
        client.websocket_connect("/ws/ui?role=operator") as op,
    ):
        until(app, "state")
        sid = start(app)
        op.send_json({"type": "end"})
        until(op, "report_ready")
    with TestClient(create_app(client.app.state.hub.directory)) as restarted:
        assert restarted.get("/report/" + sid).status_code == 200
        assert restarted.get("/session/" + sid).json()["report_status"] == "done"


def test_metrics_use_server_time():
    s = Session(started_at=100, picked_up_at=112, cpr_at=108, ended_at=130)
    assert s.metrics() == {
        "total_seconds": 30,
        "alert_to_cpr_guidance_seconds": 8,
        "alert_to_pickup_seconds": 12,
        "cpr_guidance_window_seconds": 22,
    }


def test_reconnecting_app_receives_current_prompt(client):
    with client.websocket_connect("/ws/app") as app:
        until(app, "state")
        sid = start(app)
        answer(app, "responsive")
    with client.websocket_connect("/ws/app") as app:
        assert until(app, "state")["session_id"] == sid
        assert until(app, "caller_heard")["step_id"] == "breathing"
        app.send_json({"type": "reset"})
        until(app, "override")
        assert until(app, "state")["phase"] == "idle"


def test_duplicate_producer_and_invalid_coordinates(client):
    from starlette.websockets import WebSocketDisconnect

    with client.websocket_connect("/ws/app") as app:
        until(app, "state")
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/app"):
                pass
        app.send_json({"type": "alert", "lat": 999, "lon": 0})
        assert "coordinates" in until(app, "error")["message"]
        assert client.app.state.hub.session is None


def test_audio_segments_are_retained_and_retry_is_idempotent(client, monkeypatch):
    import server.main as main

    with (
        client.websocket_connect("/ws/app") as app,
        client.websocket_connect("/ws/ui?role=operator") as op,
    ):
        until(app, "state")
        sid = start(app)
        op.send_json({"type": "pickup"})
        until(app, "pickup")
        until(app, "state")
        endpoint = f"/session/{sid}/audio?track=caller"
        headers = {"Content-Type": "audio/webm"}
        for segment in (0, 1, 1):
            result = client.post(
                endpoint + f"&segment={segment}&offset=0&duration=0",
                content=b"x" * 20,
                headers=headers,
            )
            assert result.status_code == 200
        stored = client.get("/session/" + sid).json()["audio"]["caller"]
        assert len(stored["segments"]) == 2 and stored["bytes"] == 40
        assert stored["segments"][0]["file"] != stored["segments"][1]["file"]
        assert (
            client.post(endpoint + "&segment=32", content=b"x" * 20, headers=headers).status_code
            == 400
        )
        assert (
            client.post(endpoint + "&duration=-1", content=b"x" * 20, headers=headers).status_code
            == 400
        )
        monkeypatch.setattr(main, "MAX_AUDIO", 45)
        assert (
            client.post(endpoint + "&segment=2", content=b"x" * 20, headers=headers).status_code
            == 413
        )
        assert len(client.get("/session/" + sid).json()["audio"]["caller"]["segments"]) == 2
