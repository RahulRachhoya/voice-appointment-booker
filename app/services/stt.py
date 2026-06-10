"""Speech-to-Text service using OpenAI Whisper."""
import io
from typing import Optional
import openai
from app.config import get_settings


class STTService:
    """Speech-to-Text using Whisper."""
    
    def __init__(self):
        settings = get_settings()
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = "whisper-1"
    
    async def transcribe(self, audio_bytes: bytes, language: str = "en") -> str:
        """
        Transcribe audio to text.
        
        Args:
            audio_bytes: Raw audio data (WAV/MP3)
            language: Optional language hint
        
        Returns:
            Transcribed text
        """
        # Create file-like object from bytes
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"
        
        response = self.client.audio.transcriptions.create(
            model=self.model,
            file=audio_file,
            language=language,
            response_format="text"
        )
        
        return response.strip()
    
    async def transcribe_streaming(self, chunk: bytes) -> str:
        """Transcribe streaming audio chunks (for real-time)."""
        # For real-time, would typically buffer and process
        # This is a simplified version
        return await self.transcribe(chunk)


# Singleton instance
_stt_service: Optional[STTService] = None


def get_stt_service() -> STTService:
    """Get STT service instance."""
    global _stt_service
    if _stt_service is None:
        _stt_service = STTService()
    return _stt_service