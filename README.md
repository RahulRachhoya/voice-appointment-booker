# Voice AI Appointment Booker

![CI](https://github.com/RahulRachhoya/voice-appointment-booker/workflows/CI/badge.svg)
![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![HF Spaces](https://img.shields.io/badge/demo-HF%20Spaces-orange)

An AI-powered voice agent that books appointments through natural conversation, using Groq Whisper for speech-to-text, Groq Llama-3.3 for dialogue, and ElevenLabs for text-to-speech.

---

## Architecture

```
Mic
 |
 v
VAD (silence detection)
 |
 v
Groq Whisper STT  (whisper-large-v3-turbo)
 |
 v
Groq Llama-3.3    (llama-3.3-70b-versatile)
 |
 v
ElevenLabs TTS    (eleven_flash_v2_5)
 |
 v
Speaker
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/RahulRachhoya/voice-appointment-booker.git
cd voice-appointment-booker
pip install -e ".[dev]"
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in:
#   GROQ_API_KEY=gsk_...
#   ELEVENLABS_API_KEY=...
```

### 3. Run the API server

```bash
uvicorn voice_agent.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run the Gradio demo locally

```bash
pip install gradio
cd hf_demo
python app.py
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check - returns service status |
| POST | `/api/chat/text` | Send a typed message, receive text + TTS audio |
| POST | `/api/chat/audio` | Upload audio file, receive transcript + reply |
| GET | `/api/appointments/available` | List available booking slots |
| POST | `/api/appointments/book` | Book an appointment slot |
| GET | `/api/appointments/list` | List all booked appointments |
| DELETE | `/api/appointments/{id}` | Cancel an appointment |

### Example: text chat

```bash
curl -X POST http://localhost:8000/api/chat/text \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to book an appointment for next Monday at 10am"}'
```

Response:
```json
{
  "transcript": "I need to book an appointment for next Monday at 10am",
  "response": "Sure! Could I get your name please?",
  "audio_b64": "<base64-encoded MP3>"
}
```

---

## Project Structure

```
voice-appointment-booker/
  src/voice_agent/
    config.py          # pydantic-settings BaseSettings
    models.py          # SQLModel table definitions
    pipeline.py        # Async VAD -> STT -> LLM -> TTS pipeline
    services/
      stt.py           # Groq Whisper transcription
      llm.py           # Groq Llama-3.3 dialogue
      tts.py           # ElevenLabs synthesis
      booking.py       # Slot management + BookingManager
    api/
      main.py          # FastAPI app factory
      routes/
        health.py
        chat.py
        appointments.py
  tests/
    unit/
      test_pipeline.py
      test_booking.py
  hf_demo/
    app.py             # Gradio demo for HF Spaces
    requirements.txt
  pyproject.toml
  Dockerfile
  .github/workflows/ci.yml
```

---

## Running Tests

```bash
pytest tests/unit -v
```

Tests are fully mock-based and do not require API keys.

---

## Docker

```bash
docker build -t voice-appointment-booker .
docker run -p 8000:8000 \
  -e GROQ_API_KEY=gsk_... \
  -e ELEVENLABS_API_KEY=... \
  voice-appointment-booker
```

---

## HF Spaces Demo

The `hf_demo/` directory contains a standalone Gradio app deployable to Hugging Face Spaces.

Set the following Space secrets:
- `GROQ_API_KEY`
- `ELEVENLABS_API_KEY`

---

## License

MIT
