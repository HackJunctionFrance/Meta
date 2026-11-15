import asyncio
import os
import time

from . import llm, transcription

# Illustrative case details for rehearsals and demos. Clearly tagged "Demo data" in
# the report; set FIRSTFIVE_DEMO_REPORT=0 to leave them out.
DEMO_CASE = {
    "reference": "FF-2026-0142",
    "patient": "Adult male, approx. 45–55 years (visual estimate), found on his back on the floor.",
    "history": "Witnessed collapse while standing. No complaint reported beforehand.",
    "location": "Junction 2026 venue · Hall 1, near the main stage. Indoor, well lit, floor access clear.",
    "aed": "Nearest AED at the reception desk, about 60 m away. A second bystander was sent to fetch it.",
    "resources": [
        ["Advanced life support ambulance", "Dispatched · ETA 4 min"],
        ["Fire brigade first-response unit", "Dispatched · ETA 6 min"],
    ],
    "receiving": "Cardiac arrest centre, pre-alerted for a possible incoming patient.",
    "conversation": [
        [
            "Dispatcher",
            "Emergency services. I can see what you see. You're doing great. Keep pushing, hard and fast, don't stop.",
        ],
        ["Witness", "Okay… okay."],
        [
            "Dispatcher",
            "An ambulance is on its way, four minutes. Keep going until they take over.",
        ],
        ["Witness", "Got it."],
        ["Dispatcher", "The ambulance is arriving. You can stop now. Well done."],
    ],
}


def narrative(session):
    """Plain-language summary built only from recorded events and timings."""
    m = session.metrics()
    answers = [e for e in session.timeline if e["kind"] == "answer"]
    parts = [
        "A bystander wearing FirstFive glasses raised a simulated emergency at "
        + time.strftime("%H:%M", time.localtime(session.started_at))
        + "."
    ]
    if answers:
        parts.append(
            "The witness reported the person as "
            + " and ".join(
                f"{e['label'].replace(' (reported)', '').lower()} (+{e['t']:.1f} s)"
                for e in answers
            )
            + "."
        )
    if m.get("alert_to_cpr_guidance_seconds") is not None:
        parts.append(
            f"Chest-compression guidance at 110/min started {m['alert_to_cpr_guidance_seconds']:.1f} s after the alert."
        )
    if m.get("alert_to_pickup_seconds") is not None:
        parts.append(
            f"A dispatcher took over at +{m['alert_to_pickup_seconds']:.1f} s with the witness's first-person video."
        )
    parts.append(f"The call lasted {m['total_seconds']:.1f} s.")
    return " ".join(parts)


TRANSCRIPTION_BUDGET = 50


async def build(session, directory, progress):
    await progress("transcribing")
    dialogue = []
    covered = []
    semaphore = asyncio.Semaphore(2)

    async def recognize(track, segment):
        async with semaphore:
            return await transcription.transcribe(
                directory / segment["file"], track, segment["offset"]
            )

    jobs = []
    for track, recording in session.audio.items():
        segments = recording.get("segments", [recording])
        for index, segment in enumerate(segments):
            end = (
                segment["offset"] + segment["duration"]
                if segment.get("duration") is not None
                else (
                    segments[index + 1]["offset"]
                    if index + 1 < len(segments)
                    else session.elapsed(session.ended_at)
                )
            )
            jobs.append((track, segment, end, asyncio.create_task(recognize(track, segment))))
    try:
        if jobs:
            await asyncio.wait([job[3] for job in jobs], timeout=TRANSCRIPTION_BUDGET)
        for track, segment, end, task in jobs:
            if task.done() and not task.cancelled() and task.exception() is None:
                dialogue += task.result()
                covered.append((track, segment["offset"], end))
            else:
                session.warnings.append(
                    f"{track} recording transcription unavailable at {segment['offset']:.1f}s; live captions used when available."
                )
    finally:
        for *_, task in jobs:
            if not task.done():
                task.cancel()
        await asyncio.gather(*(job[3] for job in jobs), return_exceptions=True)
    # Keep captions during missing/failed recording intervals, even when another
    # segment from the same speaker was successfully transcribed.
    dialogue += [
        line
        for line in session.subtitles
        if not any(
            track == line["speaker"] and start <= line["t"] <= end for track, start, end in covered
        )
    ]
    session.dialogue = sorted(dialogue, key=lambda x: x["t"])
    important = [f for f in session.frames if f["label"] != "Scene snapshot"]
    selected = sorted(
        (important + [f for f in session.frames if f not in important])[:6],
        key=lambda f: f["t"],
    )
    images = [(directory / f["file"]).read_bytes() for f in selected]
    session.report = {
        "summary": narrative(session),
        "captions": [f["label"] for f in selected],
        "observations": [],
        "handover": [],
        "generated": False,
    }
    # Factual MIST fallback with traceable evidence, no invented injury or vital signs.
    for e in session.timeline:
        category = {"alert": "M", "answer": "S", "cpr_guided": "T"}.get(e["kind"])
        if category:
            session.report["handover"].append(
                {"category": category, "text": e["label"], "sources": [e]}
            )
    await progress("summarizing")
    try:
        session.report = await llm.summarize(session, images)
    except Exception:
        session.warnings.append("AI summary unavailable; deterministic report retained.")
    if os.getenv("FIRSTFIVE_DEMO_REPORT", "1") != "0":
        session.report.setdefault("demo", DEMO_CASE)
    session.report["started"] = time.strftime(
        "%d %b %Y · %H:%M", time.localtime(session.started_at)
    )
    session.report["frames"] = selected
    session.report["metrics"] = session.metrics()
    session.report_status = "done"
    await progress("done")
