"""Health-check route."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict[str, str]


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services={"stt": "groq-whisper", "llm": "groq-llama3", "tts": "elevenlabs"},
    )
