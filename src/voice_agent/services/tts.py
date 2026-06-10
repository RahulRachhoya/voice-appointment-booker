"""TTS service using ElevenLabs eleven_flash_v2_5."""

import logging

log = logging.getLogger(__name__)


async def synthesize(text: str) -> bytes:
    """Convert text to speech using ElevenLabs.

    Args:
        text: Text to synthesize.

    Returns:
        Raw MP3 audio bytes.

    Raises:
        RuntimeError: If synthesis fails.
    """
    try:
        from elevenlabs import AsyncElevenLabs  # type: ignore[import-untyped]

        from voice_agent.config import get_settings

        settings = get_settings()
        if not settings.elevenlabs_api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is not set")

        client = AsyncElevenLabs(api_key=settings.elevenlabs_api_key)

        audio_iter = await client.text_to_speech.convert(
            voice_id=settings.elevenlabs_voice_id,
            text=text,
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
        )

        # collect async generator
        chunks: list[bytes] = []
        async for chunk in audio_iter:
            chunks.append(chunk)

        audio_bytes = b"".join(chunks)
        log.info("TTS synthesized %d chars -> %d bytes", len(text), len(audio_bytes))
        return audio_bytes

    except Exception as exc:
        log.error("TTS synthesis failed: %s", exc)
        raise RuntimeError(f"TTS failed: {exc}") from exc
