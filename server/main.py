import asyncio
import hmac
import io
import json
import os
import time
from contextlib import asynccontextmanager
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from PIL import Image, UnidentifiedImageError

from . import llm, reporting
from .domain import PROMPTS, Session

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
MAX_IMAGE = 2 * 1024 * 1024
MAX_AUDIO = 24 * 1024 * 1024


class Hub:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.session = None
        self.clients = {}
        self.latest = None
        self.last_frame = 0
        self.last_keyframe = 0
        self.tasks = set()
        self.lock = asyncio.Lock()

    def spawn(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    def folder(self, s):
        p = self.directory / s.id
        p.mkdir(exist_ok=True)
        return p

    def save(self, s):
        path = self.folder(s) / "session.json"
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(s.json(), indent=2), encoding="utf-8")
        temp.replace(path)

    async def send(self, ws, data):
        try:
            async with asyncio.timeout(2):
                if isinstance(data, bytes):
                    await ws.send_bytes(data)
                else:
                    await ws.send_json(data)
        except Exception:
            self.clients.pop(ws, None)

    async def broadcast(self, data, roles=None):
        await asyncio.gather(
            *(
                self.send(ws, data)
                for ws, role in list(self.clients.items())
                if roles is None or role in roles
            )
        )

    def state(self):
        return (
            self.session.state()
            if self.session
            else {
                "type": "state",
                "phase": "idle",
                "session_id": None,
                "started_at": None,
                "server_now": time.time() * 1000,
                "timeline": [],
                "card": {},
                "device": {},
            }
        )

    async def publish(self):
        if self.session:
            self.save(self.session)
        await self.broadcast(self.state())

    def keyframe(self, s, label):
        if self.latest and len(s.frames) < 60:
            name = f"frames/{len(s.frames):03d}.jpg"
            (self.folder(s) / "frames").mkdir(exist_ok=True)
            (self.folder(s) / name).write_bytes(self.latest)
            s.frames.append({"t": s.elapsed(), "file": name, "label": label})
            self.last_keyframe = time.monotonic()

    async def prompt(self):
        s = self.session
        if s and s.phase == "ai_guide":
            await self.broadcast(
                {
                    "type": "caller_heard",
                    "source": "ai_guide",
                    "text": PROMPTS[s.step],
                    "step_id": s.step,
                }
            )

    async def scene_loop(self, s):
        while self.session is s and s.phase in ("ai_guide", "connected"):
            if self.latest:
                try:
                    scene = await llm.describe(self.latest)
                    if self.session is s and s.phase != "ended":
                        s.scene = scene
                        self.save(s)
                        await self.broadcast({"type": "messenger", "card": s.card()})
                except Exception:
                    pass
            await asyncio.sleep(8)

    async def report(self, s):
        async def progress(step):
            self.save(s)
            await self.broadcast({"type": "report_progress", "session_id": s.id, "step": step})

        try:
            await reporting.build(s, self.folder(s), progress)
            self.save(s)
            await self.broadcast(
                {"type": "report_ready", "session_id": s.id, "url": f"/report/{s.id}"}
            )
        except Exception:
            s.report_status = "failed"
            s.warnings.append("Report generation failed. Saved event record is still available.")
            self.save(s)
            await progress("failed")

    async def message(self, data, role):
        if not isinstance(data, dict):
            raise ValueError("JSON object required")
        kind = data.get("type")
        allowed = {
            "app": {"alert", "answer", "guide_step", "cpr_started", "status", "reset"},
            "operator": {"pickup", "dispatcher_said", "end", "override"},
        }
        if kind not in allowed.get(role, set()):
            raise ValueError("This role cannot send that command")
        if kind == "reset":
            return await self.message({"type": "override", "action": "reset"}, "operator")
        if kind == "override":
            action = data.get("action")
            if action == "reset":
                if self.session and self.session.phase != "ended":
                    self.session.phase = "ended"
                    self.session.ended_at = time.time()
                    self.session.event("reset", "Session cancelled by operator")
                    self.save(self.session)
                self.session = None
                self.latest = None
                await self.broadcast({"type": "override", "action": "reset"})
                await self.publish()
                return
            if action == "trigger":
                return await self.message({"type": "alert", "trigger": "operator"}, "app")
            if action in ("answer_yes", "answer_no"):
                if not self.session:
                    raise ValueError("No active session")
                return await self.message(
                    {
                        "type": "answer",
                        "step_id": self.session.step,
                        "value": action.split("_")[1],
                    },
                    "app",
                )
            if action == "next_step":
                # Repeats the current prompt; never invent a negative medical answer.
                return await self.prompt()
            raise ValueError("Unknown override")
        if kind == "alert":
            if self.session and self.session.phase != "ended":
                raise ValueError("An intervention is already active")
            lat, lon = data.get("lat"), data.get("lon")
            location = {}
            if lat is not None or lon is not None:
                if (
                    not isinstance(lat, (int, float))
                    or not isinstance(lon, (int, float))
                    or not -90 <= lat <= 90
                    or not -180 <= lon <= 180
                ):
                    raise ValueError("Invalid coordinates")
                location = {"lat": lat, "lon": lon}
            self.session = Session(location=location)
            self.latest = None
            self.last_frame = 0
            self.last_keyframe = 0
            self.session.event("alert", "Simulated emergency activated by witness")
            await self.publish()
            await self.prompt()
            self.spawn(self.scene_loop(self.session))
            return
        s = self.session
        if not s or s.phase == "ended":
            raise ValueError("No active intervention")
        if kind == "answer":
            s.answer(data.get("step_id"), data.get("value"))
            self.keyframe(s, s.timeline[-1]["label"])
            await self.publish()
            await self.prompt()
            return
        if kind == "pickup":
            if s.phase == "connected":
                return
            s.phase = "connected"
            s.picked_up_at = time.time()
            s.event("pickup", "Dispatcher took over — automated guidance stopped")
            self.keyframe(s, s.timeline[-1]["label"])
            await self.broadcast({"type": "pickup"})
        elif kind == "end":
            s.phase = "ended"
            s.ended_at = time.time()
            s.event("end", "Intervention ended")
            self.keyframe(s, "End of intervention")
            s.report_status = "processing"
            await self.broadcast({"type": "end"})
            self.spawn(self.report(s))
        elif kind == "dispatcher_said":
            if s.phase != "connected":
                raise ValueError("Dispatcher has not answered")
            value = data.get("text")
            if not isinstance(value, str) or not value.strip() or len(value) > 2000:
                raise ValueError("Caption must contain 1–2000 characters")
            if data.get("final") is not True:
                return
            if len(s.subtitles) >= 2000:
                raise ValueError("Caption limit reached")
            s.subtitles.append(
                {
                    "t": s.elapsed(),
                    "speaker": "dispatcher",
                    "text": value,
                    "source": "live caption",
                }
            )
            await self.broadcast({"type": "caller_heard", "source": "dispatcher", "text": value})
        elif kind == "status":
            s.device = {k: data[k] for k in ("glasses", "battery", "stream") if k in data}
        elif kind in ("guide_step", "cpr_started"):
            # Guidance is authoritative on the server; never trust client timestamps or duplicate starts.
            return
        await self.publish()

    async def frame(self, data):
        s = self.session
        if not s or s.phase not in ("ai_guide", "connected"):
            return
        if len(data) > MAX_IMAGE:
            raise ValueError("Frame exceeds 2 MB")
        now = time.monotonic()
        if now - self.last_frame < 1 / 3:
            return
        try:
            with Image.open(io.BytesIO(data)) as img:
                if img.format != "JPEG" or img.width * img.height > 4_000_000:
                    raise ValueError("Expected JPEG below 4 megapixels")
                img.verify()
        except (UnidentifiedImageError, OSError) as e:
            raise ValueError("Invalid JPEG") from e
        self.latest = data
        self.last_frame = now
        if now - self.last_keyframe >= 10:
            self.keyframe(s, "Scene snapshot")
            self.save(s)
        await self.broadcast(data, {"operator", "viewer", "caller"})


def create_app(data_dir=None):
    hub = Hub(data_dir or os.getenv("DATA_DIR", ROOT / "data"))

    @asynccontextmanager
    async def lifespan(app):
        yield
        for task in list(hub.tasks):
            task.cancel()
        await asyncio.gather(*hub.tasks, return_exceptions=True)

    app = FastAPI(lifespan=lifespan)
    app.state.hub = hub
    templates = Environment(
        loader=FileSystemLoader(ROOT / "web"), autoescape=select_autoescape(["html"])
    )

    def authorized(key):
        expected = os.getenv("FIRSTFIVE_ACCESS_KEY", "")
        return not expected or hmac.compare_digest(str(key or ""), expected)

    @app.middleware("http")
    async def auth(request, call_next):
        key = (
            request.headers.get("X-FirstFive-Key")
            or request.cookies.get("ff_key")
            or request.query_params.get("key")
        )
        if not authorized(key):
            return JSONResponse({"detail": "Access key required"}, status_code=401)
        response = await call_next(request)
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        if request.query_params.get("key") and authorized(key):
            response.set_cookie(
                "ff_key",
                key,
                httponly=True,
                samesite="strict",
                secure=request.url.scheme == "https",
            )
        return response

    app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "demo": True,
            "livekit": all(
                os.getenv(x) for x in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET")
            ),
            "llm": os.getenv("LLM_PROVIDER", "none"),
            "transcription": bool(os.getenv("OPENAI_API_KEY")),
        }

    @app.get("/")
    @app.get("/console")
    async def console():
        return FileResponse(ROOT / "web/console.html")

    @app.get("/caller")
    async def caller():
        return FileResponse(ROOT / "web/caller.html")

    @app.get("/test-caller")
    async def test_caller():
        return FileResponse(ROOT / "web/test-caller.html")

    def saved(sid):
        if len(sid) != 32 or any(c not in "0123456789abcdef" for c in sid):
            raise HTTPException(404, "Unknown session")
        if hub.session and hub.session.id == sid:
            return hub.session.json()
        path = hub.directory / sid / "session.json"
        if not path.exists():
            raise HTTPException(404, "Unknown session")
        return json.loads(path.read_text())

    @app.get("/session/{sid}")
    async def session(sid: str):
        return saved(sid)

    @app.get("/report/{sid}", response_class=HTMLResponse)
    async def report(sid: str):
        s = saved(sid)
        return templates.get_template("report.html").render(s=s, report=s.get("report"))

    @app.get("/session/{sid}/frames/{filename}")
    async def frame(sid: str, filename: str):
        s = saved(sid)
        if not any(f["file"] == f"frames/{filename}" for f in s["frames"]):
            raise HTTPException(404, "Unknown frame")
        return FileResponse(hub.directory / sid / "frames" / filename, media_type="image/jpeg")

    @app.get("/livekit/token")
    async def token(role: str):
        if role not in ("caller", "dispatcher"):
            raise HTTPException(400, "Invalid role")
        s = hub.session
        if not s or s.phase != "connected":
            raise HTTPException(409, "No connected intervention")
        if not all(os.getenv(k) for k in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET")):
            raise HTTPException(
                503, "LiveKit not configured. Captions and local demo remain available."
            )
        from livekit import api

        jwt = (
            api.AccessToken(os.environ["LIVEKIT_API_KEY"], os.environ["LIVEKIT_API_SECRET"])
            .with_identity(role)
            .with_name(role)
            .with_ttl(timedelta(minutes=30))
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=f"firstfive-{s.id}",
                    can_publish=True,
                    can_subscribe=True,
                )
            )
            .to_jwt()
        )
        return {"token": jwt, "url": os.environ["LIVEKIT_URL"], "session_id": s.id}

    @app.post("/session/{sid}/audio")
    async def audio(
        sid: str,
        request: Request,
        track: str,
        offset: float = 0,
        segment: int = 0,
        duration: float | None = None,
    ):
        s = hub.session
        if not s or s.id != sid or s.phase != "connected":
            raise HTTPException(409, "Upload before ending the active intervention")
        if track not in ("caller", "dispatcher"):
            raise HTTPException(400, "Invalid track")
        if not 0 <= offset <= s.elapsed() + 5:
            raise HTTPException(400, "Invalid recording offset")
        if not 0 <= segment < 32:
            raise HTTPException(400, "Invalid recording segment")
        if duration is not None and not 0 <= duration <= s.elapsed() + 5 - offset:
            raise HTTPException(400, "Invalid recording duration")
        mime = request.headers.get("content-type", "").split(";")[0]
        ext = {
            "audio/webm": "webm",
            "video/webm": "webm",
            "audio/mp4": "m4a",
            "audio/ogg": "ogg",
            "audio/wav": "wav",
        }.get(mime)
        if not ext:
            raise HTTPException(415, "Unsupported recording format")
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAX_AUDIO:
                raise HTTPException(413, "Audio exceeds 24 MB")
        if len(body) < 16:
            raise HTTPException(400, "Empty recording")
        async with hub.lock:
            if hub.session is not s or s.phase != "connected":
                raise HTTPException(409, "Session ended during upload")
            previous = s.audio.get(track, {})
            segments = [r for r in previous.get("segments", []) if r["segment"] != segment]
            if sum(r["bytes"] for r in segments) + len(body) > MAX_AUDIO:
                raise HTTPException(413, "Total audio for this speaker exceeds 24 MB")
            name = f"{track}-{segment:03d}.{ext}"
            (hub.folder(s) / name).write_bytes(body)
            segments.append(
                {
                    "segment": segment,
                    "file": name,
                    "offset": offset,
                    "duration": duration,
                    "bytes": len(body),
                }
            )
            segments.sort(key=lambda r: r["segment"])
            # Preserve original metadata keys for older consumers of /session/{id}.
            s.audio[track] = {
                **segments[0],
                "bytes": sum(r["bytes"] for r in segments),
                "segments": segments,
            }
            hub.save(s)
            return {"stored": True, "track": track, "segment": segment}

    async def socket(ws, role):
        key = (
            ws.headers.get("X-FirstFive-Key")
            or ws.cookies.get("ff_key")
            or ws.query_params.get("key")
        )
        origin = ws.headers.get("origin")
        if origin and origin.split("://")[-1] != ws.headers.get("host"):
            await ws.close(code=1008)
            return
        if not authorized(key) or role not in ("app", "operator", "viewer", "caller"):
            await ws.close(code=1008)
            return
        if role == "app" and "app" in hub.clients.values():
            await ws.close(code=1008, reason="One app producer at a time")
            return
        await ws.accept()
        hub.clients[ws] = role
        await hub.send(ws, hub.state())
        if hub.latest and role != "app":
            await hub.send(ws, hub.latest)
        if role == "app" and hub.session and hub.session.phase == "ai_guide":
            await hub.send(
                ws,
                {
                    "type": "caller_heard",
                    "source": "ai_guide",
                    "text": PROMPTS[hub.session.step],
                    "step_id": hub.session.step,
                },
            )
        try:
            while True:
                packet = await ws.receive()
                if packet["type"] == "websocket.disconnect":
                    break
                try:
                    async with hub.lock:
                        if packet.get("bytes") is not None:
                            if role != "app":
                                raise ValueError("Only app can publish frames")
                            await hub.frame(packet["bytes"])
                        else:
                            if len(packet.get("text", "")) > 8192:
                                raise ValueError("Message too large")
                            await hub.message(json.loads(packet["text"]), role)
                except (ValueError, TypeError, KeyError) as error:
                    await hub.send(ws, {"type": "error", "message": str(error)})
        except WebSocketDisconnect:
            pass
        finally:
            hub.clients.pop(ws, None)

    @app.websocket("/ws/app")
    async def app_socket(ws: WebSocket):
        await socket(ws, "app")

    @app.websocket("/ws/ui")
    async def ui_socket(ws: WebSocket):
        await socket(ws, ws.query_params.get("role", "viewer"))

    return app


app = create_app()
