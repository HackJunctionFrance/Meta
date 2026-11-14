import asyncio
import os


async def transcribe(path, track, offset):
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Transcription not configured")
    from openai import AsyncOpenAI

    async with asyncio.timeout(40):
        async with AsyncOpenAI(max_retries=0) as client:
            with path.open("rb") as audio:
                result = await client.audio.transcriptions.create(
                    model=os.getenv("TRANSCRIPTION_MODEL", "whisper-1"),
                    file=audio,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                    language="en",
                )
    if not result.segments:
        raise ValueError("No timestamped speech segments returned")
    return [
        {
            "t": round(offset + s.start, 3),
            "end": round(offset + s.end, 3),
            "speaker": track,
            "text": s.text,
            "source": "recording",
        }
        for s in result.segments
    ]
