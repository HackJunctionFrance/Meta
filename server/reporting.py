import asyncio

from . import llm, transcription

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
        "summary": "Deterministic incident record. See reported observations and timeline below.",
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
    session.report["frames"] = selected
    session.report["metrics"] = session.metrics()
    session.report_status = "done"
    await progress("done")
