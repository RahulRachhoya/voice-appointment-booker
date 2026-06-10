"""Pipecat-inspired async voice pipeline: Audio -> STT -> LLM -> TTS."""

import base64
import logging
from typing import Any

log = logging.getLogger(__name__)


class VoicePipeline:
    """End-to-end voice processing pipeline.

    Frame flow:
        audio_bytes -> VAD (length check) -> Groq STT -> Groq LLM -> ElevenLabs TTS

    Usage::

        pipeline = VoicePipeline()
        result = await pipeline.process(audio_bytes)
        # result = {"transcript": "...", "response": "...", "audio_b64": "..."}
    """

    def __init__(self) -> None:
        self.history: list[dict[str, Any]] = []
        self._min_audio_bytes = 1024  # ~0.03s of 16-bit 16kHz mono

    async def process(self, audio_bytes: bytes) -> dict[str, Any]:
        """Run a full STT -> LLM -> TTS pass on raw audio.

        Args:
            audio_bytes: Raw audio data from the user's microphone.

        Returns:
            Dict with keys:
                - transcript (str): What the user said.
                - response (str): The agent's text reply.
                - audio_b64 (str): Base64-encoded MP3 of the TTS reply.

        Raises:
            ValueError: If audio is too short (likely silence).
            RuntimeError: Propagated from any service layer.
        """
        if len(audio_bytes) < self._min_audio_bytes:
            raise ValueError("Audio too short - possible silence or empty clip")

        log.debug("Pipeline received %d audio bytes", len(audio_bytes))

        # --- Stage 1: STT ---
        from voice_agent.services import stt

        transcript = await stt.transcribe(audio_bytes)
        if not transcript:
            transcript = "(inaudible)"
        log.info("STT: %r", transcript)

        # --- Stage 2: LLM ---
        from voice_agent.services import llm

        response = await llm.respond(transcript, self.history)
        log.info("LLM: %r", response)

        # Update conversation history
        self.history.append({"role": "user", "content": transcript})
        self.history.append({"role": "assistant", "content": response})

        # --- Stage 3: TTS ---
        from voice_agent.services import tts

        audio_out = await tts.synthesize(response)
        audio_b64 = base64.b64encode(audio_out).decode("utf-8")
        log.info("TTS: %d bytes encoded to %d b64 chars", len(audio_out), len(audio_b64))

        return {
            "transcript": transcript,
            "response": response,
            "audio_b64": audio_b64,
        }

    async def process_text(self, text: str) -> dict[str, Any]:
        """Skip STT and run LLM -> TTS directly on a text input.

        Useful for the typed-input fallback in the Gradio demo.

        Args:
            text: User's typed message.

        Returns:
            Same dict structure as :meth:`process` but transcript == text.
        """
        log.debug("process_text: %r", text)

        from voice_agent.services import llm, tts

        response = await llm.respond(text, self.history)
        self.history.append({"role": "user", "content": text})
        self.history.append({"role": "assistant", "content": response})

        audio_out = await tts.synthesize(response)
        audio_b64 = base64.b64encode(audio_out).decode("utf-8")

        return {
            "transcript": text,
            "response": response,
            "audio_b64": audio_b64,
        }

    def reset(self) -> None:
        """Clear conversation history."""
        self.history.clear()
        log.debug("Pipeline history reset")
