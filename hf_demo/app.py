"""Gradio demo for Voice AI Appointment Booker - deployable to HF Spaces.

Required Secrets (set in HF Space settings):
  GROQ_API_KEY
  ELEVENLABS_API_KEY

Optional:
  ELEVENLABS_VOICE_ID  (default: Rachel - 21m00Tcm4TlvDq8ikWAM)
"""

from __future__ import annotations

import base64
import io
import logging
import os
import tempfile
from typing import Any

import gradio as gr
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Settings (read from env / HF Space secrets)
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

SYSTEM_PROMPT = """You are a professional appointment booking assistant for a healthcare clinic.
Your role:
- Greet callers warmly and help them book, cancel, or reschedule appointments.
- Collect required info: customer name, preferred date, preferred time, service type.
- Confirm details before finalising.
- Keep responses short (1-3 sentences), suitable for speech.
Services: Initial consultation, Follow-up visit, Standard appointment, Emergency slot.
Available: Monday-Friday 9am-5pm, Saturday 10am-2pm."""

# ---------------------------------------------------------------------------
# Service helpers
# ---------------------------------------------------------------------------


async def _transcribe(audio_bytes: bytes) -> str:
    """Transcribe audio using Groq Whisper."""
    if not GROQ_API_KEY:
        return "[GROQ_API_KEY not set - transcription unavailable]"
    try:
        import groq

        client = groq.AsyncGroq(api_key=GROQ_API_KEY)
        buf = io.BytesIO(audio_bytes)
        buf.name = "audio.wav"
        result = await client.audio.transcriptions.create(
            file=buf,
            model="whisper-large-v3-turbo",
            response_format="text",
        )
        return (result if isinstance(result, str) else str(result)).strip()
    except Exception as exc:
        log.error("STT error: %s", exc)
        return f"[STT error: {exc}]"


async def _respond(text: str, history: list[dict[str, Any]]) -> str:
    """Get LLM reply from Groq Llama-3.3-70b."""
    if not GROQ_API_KEY:
        return "[GROQ_API_KEY not set - LLM unavailable]"
    try:
        import groq

        client = groq.AsyncGroq(api_key=GROQ_API_KEY)
        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in history[-10:]:
            messages.append({"role": str(turn["role"]), "content": str(turn["content"])})
        messages.append({"role": "user", "content": text})
        completion = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,  # type: ignore[arg-type]
            max_tokens=256,
            temperature=0.7,
        )
        return (completion.choices[0].message.content or "").strip()
    except Exception as exc:
        log.error("LLM error: %s", exc)
        return f"[LLM error: {exc}]"


async def _synthesize(text: str) -> bytes | None:
    """Convert text to speech using ElevenLabs."""
    if not ELEVENLABS_API_KEY:
        log.warning("ELEVENLABS_API_KEY not set - skipping TTS")
        return None
    try:
        from elevenlabs import AsyncElevenLabs

        client = AsyncElevenLabs(api_key=ELEVENLABS_API_KEY)
        audio_iter = await client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            text=text,
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
        )
        chunks: list[bytes] = []
        async for chunk in audio_iter:
            chunks.append(chunk)
        return b"".join(chunks)
    except Exception as exc:
        log.error("TTS error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Shared conversation state (module-level for simplicity)
# ---------------------------------------------------------------------------
_history: list[dict[str, Any]] = []


def _reset_history() -> None:
    global _history
    _history = []


# ---------------------------------------------------------------------------
# Gradio handlers
# ---------------------------------------------------------------------------


async def handle_audio(audio_path: str | None) -> tuple[list, str, str | None]:
    """Handle microphone/upload audio input.

    Returns:
        (chatbot_history, status_text, tts_audio_path)
    """
    if not audio_path:
        return _history_to_chatbot(), "No audio received.", None

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    status = f"Received {len(audio_bytes):,} bytes of audio. Transcribing..."
    transcript = await _transcribe(audio_bytes)
    if not transcript or transcript.startswith("["):
        status = f"Transcription result: {transcript}"
        return _history_to_chatbot(), status, None

    status = f"You said: {transcript}\nGenerating response..."
    response = await _respond(transcript, _history)
    _history.append({"role": "user", "content": transcript})
    _history.append({"role": "assistant", "content": response})

    audio_path_out = await _make_audio_file(response)
    status = f"Transcript: {transcript}"
    return _history_to_chatbot(), status, audio_path_out


async def handle_text(text: str) -> tuple[list, str, str | None]:
    """Handle typed text input.

    Returns:
        (chatbot_history, status_text, tts_audio_path)
    """
    if not text.strip():
        return _history_to_chatbot(), "Please type a message.", None

    response = await _respond(text.strip(), _history)
    _history.append({"role": "user", "content": text.strip()})
    _history.append({"role": "assistant", "content": response})

    audio_path_out = await _make_audio_file(response)
    return _history_to_chatbot(), f"Sent: {text.strip()}", audio_path_out


async def _make_audio_file(text: str) -> str | None:
    """Synthesize text and save to a temp file for Gradio Audio output."""
    audio_bytes = await _synthesize(text)
    if not audio_bytes:
        return None
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.write(audio_bytes)
    tmp.close()
    return tmp.name


def _history_to_chatbot() -> list[tuple[str, str]]:
    """Convert history list to Gradio Chatbot format (list of (user, bot) tuples)."""
    pairs: list[tuple[str, str]] = []
    i = 0
    while i < len(_history) - 1:
        if _history[i]["role"] == "user" and _history[i + 1]["role"] == "assistant":
            pairs.append((_history[i]["content"], _history[i + 1]["content"]))
            i += 2
        else:
            i += 1
    return pairs


def reset_conversation() -> tuple[list, str, None]:
    """Clear conversation history."""
    _reset_history()
    return [], "Conversation reset.", None


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="Voice AI Appointment Booker", theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
# Voice AI Appointment Booker
**AI-powered voice agent for booking appointments** | Groq Whisper STT + Llama-3.3 LLM + ElevenLabs TTS

Use the microphone or type your message below.
"""
    )

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Input")
            audio_input = gr.Audio(
                sources=["microphone", "upload"],
                type="filepath",
                label="Speak or upload audio",
            )
            submit_audio_btn = gr.Button("Process Audio", variant="primary")

            gr.Markdown("#### Or type your message")
            text_input = gr.Textbox(
                placeholder="e.g. I'd like to book an appointment for next Tuesday at 10am",
                label="Typed input",
                lines=2,
            )
            submit_text_btn = gr.Button("Send Text", variant="secondary")
            reset_btn = gr.Button("Reset Conversation", variant="stop")

        with gr.Column(scale=2):
            gr.Markdown("### Conversation")
            chatbot = gr.Chatbot(label="Chat History", height=400)
            audio_output = gr.Audio(
                label="Agent Voice Response",
                type="filepath",
                autoplay=True,
            )
            status_box = gr.Textbox(label="Status / Debug", lines=2, interactive=False)

    # Wire up events
    submit_audio_btn.click(
        fn=handle_audio,
        inputs=[audio_input],
        outputs=[chatbot, status_box, audio_output],
    )

    submit_text_btn.click(
        fn=handle_text,
        inputs=[text_input],
        outputs=[chatbot, status_box, audio_output],
    )

    text_input.submit(
        fn=handle_text,
        inputs=[text_input],
        outputs=[chatbot, status_box, audio_output],
    )

    reset_btn.click(
        fn=reset_conversation,
        inputs=[],
        outputs=[chatbot, status_box, audio_output],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
