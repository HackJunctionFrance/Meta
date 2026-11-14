import json

import pytest

from server import llm, reporting, transcription
from server.domain import Session


@pytest.mark.asyncio
async def test_model_json_and_source_validation(monkeypatch):
    s = Session()
    s.event("alert", "Alert triggered")

    async def complete(*args, **kwargs):
        return json.dumps(
            {
                "summary": "Observed incident",
                "captions": [],
                "observations": ["Person lying down"],
                "handover": [
                    {"category": "M", "text": "Alert triggered", "source_ids": ["e0"]},
                    {
                        "category": "S",
                        "text": "Invented vital sign",
                        "source_ids": ["missing"],
                    },
                ],
            }
        )

    monkeypatch.setattr(llm, "complete", complete)
    result = await llm.summarize(s, [])
    assert len(result["handover"]) == 1
    assert result["handover"][0]["sources"][0]["kind"] == "alert"


@pytest.mark.asyncio
async def test_report_merges_offsets_and_preserves_caption_fallback(monkeypatch, tmp_path):
    s = Session()
    s.ended_at = s.started_at + 60
    s.audio = {
        "caller": {"file": "caller.webm", "offset": 12},
        "dispatcher": {"file": "dispatcher.webm", "offset": 10},
    }
    s.subtitles = [
        {
            "t": 11,
            "speaker": "dispatcher",
            "text": "Caption fallback",
            "source": "live caption",
        },
        {
            "t": 13,
            "speaker": "caller",
            "text": "Do not duplicate",
            "source": "live caption",
        },
    ]

    async def transcribe(path, track, offset):
        if track == "dispatcher":
            raise TimeoutError()
        return [
            {
                "t": offset + 2,
                "end": offset + 3,
                "speaker": track,
                "text": "Caller recording",
                "source": "recording",
            }
        ]

    async def fail(*args):
        raise TimeoutError()

    async def progress(step):
        pass

    monkeypatch.setattr(transcription, "transcribe", transcribe)
    monkeypatch.setattr(llm, "summarize", fail)
    await reporting.build(s, tmp_path, progress)
    assert [x["text"] for x in s.dialogue] == ["Caption fallback", "Caller recording"]
    assert s.dialogue[-1]["t"] == 14 and s.report_status == "done"
    assert not s.report["generated"] and len(s.warnings) == 2


@pytest.mark.asyncio
async def test_provider_none_is_explicit(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "none")
    with pytest.raises(RuntimeError):
        await llm.describe(b"jpeg")


@pytest.mark.asyncio
async def test_partial_transcription_keeps_only_uncovered_captions(monkeypatch, tmp_path):
    s = Session()
    s.ended_at = s.started_at + 30
    s.audio = {
        "dispatcher": {
            "segments": [
                {"file": "first.webm", "offset": 2, "duration": 5},
                {"file": "second.webm", "offset": 12, "duration": 5},
            ]
        }
    }
    s.subtitles = [
        {"t": t, "speaker": "dispatcher", "text": text, "source": "live caption"}
        for t, text in [
            (1, "Before recording"),
            (4, "Duplicate"),
            (9, "Between recordings"),
            (14, "Failed segment"),
        ]
    ]

    async def transcribe(path, track, offset):
        if offset == 12:
            raise TimeoutError()
        return [{"t": 3, "speaker": track, "text": "Recorded speech", "source": "recording"}]

    async def fail(*args):
        raise RuntimeError()

    async def progress(step):
        pass

    monkeypatch.setattr(transcription, "transcribe", transcribe)
    monkeypatch.setattr(llm, "summarize", fail)
    await reporting.build(s, tmp_path, progress)
    assert [line["text"] for line in s.dialogue] == [
        "Before recording",
        "Recorded speech",
        "Between recordings",
        "Failed segment",
    ]


@pytest.mark.asyncio
async def test_transcription_budget_cancels_stalled_requests(monkeypatch, tmp_path):
    import asyncio

    s = Session()
    s.ended_at = s.started_at + 10
    s.audio = {"caller": {"file": "caller.webm", "offset": 0}}
    s.subtitles = [
        {"t": 2, "speaker": "caller", "text": "Still available", "source": "live caption"}
    ]
    cancelled = []

    async def stall(*args):
        try:
            await asyncio.sleep(10)
        finally:
            cancelled.append(True)

    async def fail(*args):
        raise RuntimeError()

    async def progress(step):
        pass

    monkeypatch.setattr(reporting, "TRANSCRIPTION_BUDGET", 0.02)
    monkeypatch.setattr(transcription, "transcribe", stall)
    monkeypatch.setattr(llm, "summarize", fail)
    await asyncio.wait_for(reporting.build(s, tmp_path, progress), 1)
    assert cancelled == [True] and s.report_status == "done"
    assert s.dialogue[0]["text"] == "Still available"
