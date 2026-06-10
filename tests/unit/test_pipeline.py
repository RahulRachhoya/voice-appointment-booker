"""Unit tests for VoicePipeline (mock-based, no API keys required)."""

import base64
from unittest.mock import AsyncMock, patch

import pytest

from voice_agent.pipeline import VoicePipeline


@pytest.fixture
def pipeline():
    """Return a fresh VoicePipeline."""
    return VoicePipeline()


@pytest.mark.asyncio
async def test_process_returns_expected_keys(pipeline: VoicePipeline):
    """process() should return dict with transcript, response, audio_b64."""
    fake_audio = b"\x00" * 2048  # enough bytes to pass VAD check
    fake_transcript = "I'd like to book an appointment"
    fake_response = "Sure, what date works for you?"
    fake_audio_out = b"FAKEMP3BYTES"

    with (
        patch("voice_agent.services.stt.transcribe", new=AsyncMock(return_value=fake_transcript)),
        patch("voice_agent.services.llm.respond", new=AsyncMock(return_value=fake_response)),
        patch("voice_agent.services.tts.synthesize", new=AsyncMock(return_value=fake_audio_out)),
    ):
        result = await pipeline.process(fake_audio)

    assert result["transcript"] == fake_transcript
    assert result["response"] == fake_response
    assert result["audio_b64"] == base64.b64encode(fake_audio_out).decode()


@pytest.mark.asyncio
async def test_process_too_short_raises_value_error(pipeline: VoicePipeline):
    """process() should raise ValueError when audio is too short."""
    with pytest.raises(ValueError, match="Audio too short"):
        await pipeline.process(b"\x00" * 100)  # below 1024-byte threshold


@pytest.mark.asyncio
async def test_process_text_skips_stt(pipeline: VoicePipeline):
    """process_text() should not call stt.transcribe."""
    fake_response = "I can help you with that."
    fake_audio_out = b"MP3DATA"

    with (
        patch("voice_agent.services.stt.transcribe", new=AsyncMock()) as mock_stt,
        patch("voice_agent.services.llm.respond", new=AsyncMock(return_value=fake_response)),
        patch("voice_agent.services.tts.synthesize", new=AsyncMock(return_value=fake_audio_out)),
    ):
        result = await pipeline.process_text("Hello")

    mock_stt.assert_not_called()
    assert result["transcript"] == "Hello"
    assert result["response"] == fake_response


@pytest.mark.asyncio
async def test_history_accumulates_across_calls(pipeline: VoicePipeline):
    """History should grow by 2 entries per turn (user + assistant)."""
    fake_audio = b"\x00" * 2048

    with (
        patch("voice_agent.services.stt.transcribe", new=AsyncMock(return_value="turn 1")),
        patch("voice_agent.services.llm.respond", new=AsyncMock(return_value="reply 1")),
        patch("voice_agent.services.tts.synthesize", new=AsyncMock(return_value=b"audio")),
    ):
        await pipeline.process(fake_audio)

    assert len(pipeline.history) == 2

    with (
        patch("voice_agent.services.stt.transcribe", new=AsyncMock(return_value="turn 2")),
        patch("voice_agent.services.llm.respond", new=AsyncMock(return_value="reply 2")),
        patch("voice_agent.services.tts.synthesize", new=AsyncMock(return_value=b"audio")),
    ):
        await pipeline.process(fake_audio)

    assert len(pipeline.history) == 4


@pytest.mark.asyncio
async def test_reset_clears_history(pipeline: VoicePipeline):
    """reset() should clear conversation history."""
    fake_audio = b"\x00" * 2048

    with (
        patch("voice_agent.services.stt.transcribe", new=AsyncMock(return_value="hello")),
        patch("voice_agent.services.llm.respond", new=AsyncMock(return_value="hi")),
        patch("voice_agent.services.tts.synthesize", new=AsyncMock(return_value=b"audio")),
    ):
        await pipeline.process(fake_audio)

    assert len(pipeline.history) > 0
    pipeline.reset()
    assert pipeline.history == []


@pytest.mark.asyncio
async def test_stt_returns_inaudible_on_empty_transcript(pipeline: VoicePipeline):
    """When STT returns empty string, transcript should be '(inaudible)'."""
    with (
        patch("voice_agent.services.stt.transcribe", new=AsyncMock(return_value="")),
        patch("voice_agent.services.llm.respond", new=AsyncMock(return_value="Sorry, I missed that.")),
        patch("voice_agent.services.tts.synthesize", new=AsyncMock(return_value=b"audio")),
    ):
        result = await pipeline.process(b"\x00" * 2048)

    assert result["transcript"] == "(inaudible)"
