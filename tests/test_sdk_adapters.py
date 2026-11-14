"""Official SDK requests intercepted by httpx; no vendor credentials or network required."""

import io

import httpx2 as httpx
import pytest
from PIL import Image

from server import llm, transcription


def jpeg():
    buf = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buf, "JPEG")
    return buf.getvalue()


@pytest.mark.asyncio
async def test_anthropic_official_sdk(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    async def send(self, request, **kwargs):
        assert request.url.path == "/v1/messages"
        assert b"image/jpeg" in request.content and b"test-model" in request.content
        return httpx.Response(
            200,
            request=request,
            json={
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "model": "test-model",
                "content": [{"type": "text", "text": "Person lying on the floor."}],
                "stop_reason": "end_turn",
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    assert await llm.describe(jpeg()) == "Person lying on the floor."


@pytest.mark.asyncio
async def test_gemini_official_sdk(monkeypatch):
    import google.genai._api_client as api_client

    monkeypatch.setattr(api_client, "has_aiohttp", False)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    # google-genai may use aiohttp when installed; this project uses the default httpx transport.
    async def send(self, request, **kwargs):
        assert "test-model:generateContent" in str(request.url)
        assert b"image/jpeg" in request.content
        return httpx.Response(
            200,
            request=request,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "Indoor scene."}],
                            "role": "model",
                        },
                        "finishReason": "STOP",
                    }
                ]
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    assert await llm.describe(jpeg()) == "Indoor scene."


@pytest.mark.asyncio
async def test_openai_timestamped_segments(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    path = tmp_path / "audio.webm"
    path.write_bytes(b"synthetic audio fixture")

    async def send(self, request, **kwargs):
        body = await request.aread()
        assert b"timestamp_granularities" in body and b"verbose_json" in body
        return httpx.Response(
            200,
            request=request,
            json={
                "task": "transcribe",
                "language": "english",
                "duration": 4,
                "text": "Keep pushing",
                "segments": [
                    {
                        "id": 0,
                        "seek": 0,
                        "start": 1.5,
                        "end": 3.0,
                        "text": "Keep pushing",
                        "tokens": [],
                        "temperature": 0,
                        "avg_logprob": 0,
                        "compression_ratio": 1,
                        "no_speech_prob": 0,
                    }
                ],
            },
        )

    monkeypatch.setattr(httpx.AsyncClient, "send", send)
    lines = await transcription.transcribe(path, "dispatcher", 12)
    assert lines[0]["t"] == 13.5 and lines[0]["end"] == 15 and lines[0]["speaker"] == "dispatcher"
