"""STT service using Groq Whisper."""

import io
import logging

log = logging.getLogger(__name__)


async def transcribe(audio_bytes: bytes, filename: str | None = "audio.wav") -> str:
    """Transcribe audio bytes to text using Groq Whisper.

    Args:
        audio_bytes: Raw audio data (WAV, MP3, OGG, etc.)
        filename: Filename hint so Groq knows the format.

    Returns:
        Transcribed text string.

    Raises:
        RuntimeError: If transcription fails.
    """
    try:
        import groq  # type: ignore[import-untyped]

        from voice_agent.config import get_settings

        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set")

        client = groq.AsyncGroq(api_key=settings.groq_api_key)

        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename or "audio.wav"

        transcription = await client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
            response_format="text",
        )

        text = transcription if isinstance(transcription, str) else str(transcription)
        log.info("Transcribed %d bytes -> %d chars", len(audio_bytes), len(text))
        return text.strip()

    except Exception as exc:
        log.error("STT transcription failed: %s", exc)
        raise RuntimeError(f"STT failed: {exc}") from exc
