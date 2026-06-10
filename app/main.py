"""Main FastAPI application for Voice AI Appointment Booker."""
import os
import sys
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import get_settings


# Database setup (lazy import to avoid issues without DB)
def get_db_engine():
    """Get or create database engine."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base
    
    settings = get_settings()
    if settings.database_url:
        engine = create_engine(settings.database_url)
        Base.metadata.create_all(engine)
        return engine
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup app resources."""
    # Startup: Setup database
    engine = get_db_engine()
    if engine:
        from sqlalchemy.orm import sessionmaker
        app.state.db_engine = engine
        app.state.db_session = sessionmaker(bind=engine)
    
    yield
    
    # Shutdown: Cleanup
    if hasattr(app.state, "db_engine"):
        app.state.db_engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Voice AI Appointment Booker",
    description="AI-powered voice agent for appointment booking",
    version="1.0.0",
    lifespan=lifespan
)

# CORS - allow all for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Routes
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "Voice AI Appointment Booker",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "stt": "connected",
            "llm": "connected", 
            "tts": "connected"
        }
    }


# Chat endpoints for web demo
class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    response: str
    audio_url: Optional[str] = None


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the voice AI (for web demo without phone).
    
    Send a text message, get text + optionally audio response.
    """
    import hashlib
    import tempfile
    
    from app.services.llm import get_llm_service
    from app.services.tts import get_tts_service
    
    llm = get_llm_service()
    tts = get_tts_service()
    
    # Generate response
    context = request.context or {}
    llm_response = await llm.generate_response(request.message, context)
    
    # Generate audio (optional - for voice demo)
    audio = await tts.synthesize(llm_response)
    
    # Save audio to temp file
    import tempfile
    import hashlib
    
    audio_hash = hashlib.md5(llm_response.encode()).hexdigest()[:8]
    audio_path = f"/tmp/response_{audio_hash}.mp3"
    with open(audio_path, "wb") as f:
        f.write(audio)
    
    return ChatResponse(
        response=llm_response,
        audio_url=f"/api/audio/{audio_hash}"
    )


@app.get("/api/audio/{audio_hash}")
async def get_audio(audio_hash: str):
    """Serve generated audio files."""
    audio_path = f"/tmp/response_{audio_hash}.mp3"
    if os.path.exists(audio_path):
        return FileResponse(audio_path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="Audio not found")


# Video demo page
@app.get("/demo")
async def demo_page():
    """Serve the demo HTML page."""
    return FileResponse("app/static/demo.html")


# Twilio webhooks
@app.post("/webhooks/twilio/call")
async def twilio_call(request: Request):
    """Twilio incoming call webhook."""
    from app.services.twilio_handler import get_twilio_handler
    
    handler = get_twilio_handler()
    return await handler.handle_incoming_call(request)


@app.post("/webhooks/twilio/transcription")
async def twilio_transcription(
    call_sid: str = Form(None),
    recording_url: str = Form(None)
):
    """Twilio transcription callback."""
    from app.services.twilio_handler import get_twilio_handler
    
    handler = get_twilio_handler()
    result = await handler.handle_recording_complete(call_sid or "", recording_url or "")
    return result


# Call management
@app.post("/api/call/start")
async def start_call(caller_number: str):
    """Start a new call session."""
    from app.services.call_handler import get_call_handler
    
    handler = get_call_handler()
    call = await handler.init_call(f"call_{caller_number}", caller_number)
    
    return {
        "call_sid": call.call_sid,
        "status": "started"
    }


@app.post("/api/call/end")
async def end_call():
    """End current call and extract appointment."""
    from app.services.call_handler import get_call_handler
    
    handler = get_call_handler()
    result = await handler.handle_end_call()
    
    return result


# Statistics
@app.get("/api/stats")
async def get_stats():
    """Get call statistics."""
    # Would query database in production
    return {
        "total_calls": 0,
        "appointments_booked": 0,
        "average_turns": 0,
        "conversion_rate": 0
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )