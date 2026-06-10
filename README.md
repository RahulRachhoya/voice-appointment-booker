# 🎙️ Voice AI Appointment Booker

A production-ready voice AI system that handles phone calls to book appointments. Built with Python, FastAPI, LangChain, and Twilio.

## Features

- **Natural Conversation**: Multi-turn dialogue with context retention
- **Calendar Integration**: Google Calendar API for real-time availability
- **Smart Handling**: Objection handling, fallback to human when confused
- **Multi-Channel**: Phone (Twilio), Web, WhatsApp
- **Analytics**: Call logging, sentiment analysis, conversion tracking

## Tech Stack

- **STT**: OpenAI Whisper
- **LLM**: Anthropic Claude via AWS Bedrock
- **TTS**: ElevenLabs or Sarvam AI
- **Backend**: FastAPI + PostgreSQL
- **Phone**: Twilio
- **Calendar**: Google Calendar API

## Quick Start

```bash
# Clone and setup
cd voice-appointment-booker
cp .env.example .env
# Edit .env with your API keys

# Install dependencies
pip install -r requirements.txt

# Run the server
python main.py
```

## Architecture

```
User Call → Twilio → FastAPI → STT → LLM → TTS → Twilio → User
                                    ↓
                             PostgreSQL (logs)
                                    ↓
                             Google Calendar (booking)
```

## Configuration

See `.env.example` for all configuration options.

## License

MIT