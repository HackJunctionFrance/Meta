"""Real local LiveKit + Chromium WebRTC + MediaRecorder integration (synthetic microphone)."""

import os

from playwright.sync_api import expect, sync_playwright

BASE = os.getenv("FIRSTFIVE_TEST_URL", "http://127.0.0.1:8001")
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.getenv("CHROMIUM_PATH", "/usr/bin/chromium"),
        headless=True,
        args=[
            "--no-sandbox",
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
            "--autoplay-policy=no-user-gesture-required",
        ],
    )
    context = browser.new_context(permissions=["microphone", "camera"])
    caller = context.new_page()
    op = context.new_page()
    errors = []
    for page in (caller, op):
        page.on("pageerror", lambda e: errors.append(str(e)))
    op.goto(BASE + "/console?mode=operator")
    caller.goto(BASE + "/test-caller")
    expect(caller.locator("#connection")).to_contain_text("Server connected")
    op.locator("#tools summary").click()
    session_ids = set()
    for rehearsal in range(2):
        op.locator('[data-action="reset"]').click()
        expect(caller.locator("#phase")).to_have_text("Waiting for a call")
        caller.locator("#emergency").click()
        expect(op.locator("#phase")).to_have_text("Incoming emergency")
        op.locator("#answer").click()
        expect(caller.locator("#phase")).to_have_text("Dispatcher connected")
        op.wait_for_function('document.querySelectorAll("audio").length === 1', timeout=30000)
        caller.wait_for_function('document.querySelectorAll("audio").length === 1', timeout=30000)
        # Both clients receive a live remote audio track over a real WebRTC connection.
        for page in (caller, op):
            assert (
                page.locator("audio").evaluate("(e)=>e.srcObject.getAudioTracks()[0].readyState")
                == "live"
            )
        op.wait_for_timeout(2500)
        if rehearsal == 1:
            # Reload the caller during a live intervention. The dispatcher must
            # retain audio before the disconnect and record the new remote track.
            caller.reload()
            expect(caller.locator("#phase")).to_have_text("Dispatcher connected")
            caller.wait_for_function(
                'document.querySelectorAll("audio").length === 1', timeout=30000
            )
            op.wait_for_function('document.querySelectorAll("audio").length === 1', timeout=30000)
            op.wait_for_timeout(2500)
        op.locator("#end").click()
        expect(op.locator("#reportLink")).to_be_visible(timeout=30000)
        sid = op.locator("#reportLink").get_attribute("href").split("/")[-1]
        record = context.request.get(BASE + "/session/" + sid).json()
        assert set(record["audio"]) == {"caller", "dispatcher"}, record
        assert all(a["bytes"] > 1000 and a["offset"] >= 0 for a in record["audio"].values()), (
            record["audio"]
        )
        assert record["report_status"] == "done"
        expected_caller_segments = 2 if rehearsal == 1 else 1
        assert len(record["audio"]["caller"]["segments"]) == expected_caller_segments
        assert len(record["audio"]["dispatcher"]["segments"]) == 1
        assert all(segment["bytes"] > 1000 for segment in record["audio"]["caller"]["segments"])
        if rehearsal == 1:
            segments = record["audio"]["caller"]["segments"]
            assert segments[1]["offset"] > segments[0]["offset"] + segments[0]["duration"] - 0.1
        assert (
            len([w for w in record["warnings"] if "transcription unavailable" in w])
            == 1 + expected_caller_segments
        )
        assert sid not in session_ids
        session_ids.add(sid)
    assert not errors, errors
    print(
        "PASS: two rehearsals including a caller reload during the live call, real local LiveKit, two bidirectional live WebRTC audio tracks, two MediaRecorder uploads, timestamp offsets, report fallback. Synthetic browser microphones; no cloud service or human speech used."
    )
    browser.close()
