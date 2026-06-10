"""Chat route - text and audio interaction."""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from voice_agent.pipeline import VoicePipeline

log = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

# Per-process pipeline singleton (stateful conversation history)
_pipeline: VoicePipeline | None = None


def _get_pipeline() -> VoicePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = VoicePipeline()
    return _pipeline


class TextChatRequest(BaseModel):
    message: str
    reset: bool = False


class ChatResponse(BaseModel):
    transcript: str
    response: str
    audio_b64: str


@router.post("/text", response_model=ChatResponse)
async def chat_text(request: TextChatRequest) -> ChatResponse:
    """Process a typed message and return text + TTS audio."""
    pipeline = _get_pipeline()
    if request.reset:
        pipeline.reset()
    try:
        result = await pipeline.process_text(request.message)
        return ChatResponse(**result)
    except RuntimeError as exc:
        log.error("chat_text error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/audio", response_model=ChatResponse)
async def chat_audio(file: UploadFile = File(...)) -> ChatResponse:  # noqa: B008
    """Process an audio upload and return transcript + TTS audio."""
    pipeline = _get_pipeline()
    try:
        audio_bytes = await file.read()
        result = await pipeline.process(audio_bytes)
        return ChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        log.error("chat_audio error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/reset")
async def reset_chat() -> dict[str, str]:
    """Reset the conversation history."""
    _get_pipeline().reset()
    return {"status": "reset"}
