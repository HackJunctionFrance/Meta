"""Run python -m server.sim_app --auto-pickup. No glasses, keys, or sample video required."""

import argparse
import asyncio
import io
import json
import os
import time
from pathlib import Path

import httpx
import websockets
from dotenv import load_dotenv
from PIL import Image, ImageDraw


async def run(args):
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    key = os.getenv("FIRSTFIVE_ACCESS_KEY", "")
    headers = {"X-FirstFive-Key": key} if key else {}
    url = args.url.rstrip("/")
    wsurl = url.replace("https://", "wss://").replace("http://", "ws://")
    async with (
        websockets.connect(wsurl + "/ws/app", additional_headers=headers) as app,
        websockets.connect(wsurl + "/ws/ui?role=operator", additional_headers=headers) as operator,
    ):
        state = {}
        done = asyncio.Event()

        async def receive():
            async for raw in app:
                if isinstance(raw, str):
                    msg = json.loads(raw)
                    if msg["type"] == "state":
                        state.update(msg)
                    if msg["type"] == "error":
                        print("Server:", msg["message"])
                    if msg["type"] == "end":
                        done.set()

        receiver = asyncio.create_task(receive())

        async def send(socket, **data):
            await socket.send(json.dumps({**data, "ts": time.time() * 1000}))

        await send(app, type="alert", lat=60.18, lon=24.83, trigger="button")

        async def frames():
            cap = None
            if args.video:
                import cv2

                cap = cv2.VideoCapture(args.video)
                if not cap.isOpened():
                    raise ValueError("Cannot open sample video")
            try:
                n = 0
                while not done.is_set():
                    if cap:
                        import cv2

                        ok, frame = cap.read()
                        if not ok:
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            ok, frame = cap.read()
                            if not ok:
                                raise ValueError("Video contains no decodable frames")
                        frame = cv2.resize(frame, (960, 540))
                        jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 50])[
                            1
                        ].tobytes()
                    else:
                        image = Image.new("RGB", (960, 540), "#142a33")
                        draw = ImageDraw.Draw(image)
                        draw.text(
                            (45, 45),
                            f"FIRSTFIVE / SYNTHETIC DEMO\nFrame {n} - no patient or glasses",
                            fill="#9aefbd",
                            font_size=30,
                        )
                        draw.ellipse((220, 280, 290, 350), outline="#a3b9c0", width=10)
                        draw.line(
                            [(290, 315), (560, 315), (700, 410)],
                            fill="#a3b9c0",
                            width=15,
                        )
                        b = io.BytesIO()
                        image.save(b, format="JPEG", quality=50)
                        jpeg = b.getvalue()
                    await app.send(jpeg)
                    n += 1
                    await asyncio.sleep(0.35)
            finally:
                if cap:
                    cap.release()

        frame_task = asyncio.create_task(frames())
        try:
            await asyncio.sleep(3 * args.speed)
            if frame_task.done():
                frame_task.result()
            await send(app, type="answer", step_id="responsive", value="no", heard="no")
            await asyncio.sleep(3 * args.speed)
            await send(app, type="answer", step_id="breathing", value="no", heard="no")
            if args.auto_pickup:
                await asyncio.sleep(4 * args.speed)
                await send(operator, type="pickup")
                await asyncio.sleep(1 * args.speed)
                await send(
                    operator,
                    type="dispatcher_said",
                    text="Simulated dispatcher: I can see the scene. Keep following my instructions.",
                    final=True,
                )
                await asyncio.sleep(4 * args.speed)
                async with httpx.AsyncClient(headers=headers) as client:
                    for track in ("caller", "dispatcher"):
                        path = getattr(args, track + "_audio")
                        if path:
                            p = Path(path)
                            mime = {
                                ".wav": "audio/wav",
                                ".webm": "audio/webm",
                                ".m4a": "audio/mp4",
                            }.get(p.suffix, "audio/webm")
                            r = await client.post(
                                f"{url}/session/{state['session_id']}/audio",
                                params={"track": track, "offset": 10 * args.speed},
                                content=p.read_bytes(),
                                headers={"Content-Type": mime},
                            )
                            r.raise_for_status()
                await send(operator, type="end")
                async for raw in operator:
                    if isinstance(raw, str):
                        msg = json.loads(raw)
                        if msg["type"] == "report_ready":
                            print("Report:", url + msg["url"])
                            break
            else:
                print("Simulator active. Answer and end in /console?mode=operator.")
                await done.wait()
        finally:
            for task in (receiver, frame_task):
                task.cancel()
            await asyncio.gather(receiver, frame_task, return_exceptions=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--video")
    parser.add_argument("--auto-pickup", action="store_true")
    parser.add_argument("--speed", type=float, default=1)
    parser.add_argument("--caller-audio")
    parser.add_argument("--dispatcher-audio")
    args = parser.parse_args()
    asyncio.run(run(args))
