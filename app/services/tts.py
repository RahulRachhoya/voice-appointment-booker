"""Text-to-Speech service using ElevenLabs."""
import io
from typing import Optional
import elevenlabs
from elevenlabs import generate, save
from app.config import get_settings


class TTSService:
    """Text-to-Speech using ElevenLabs."""
    
    def __init__(self):
        settings = get_settings()
        elevenlabs.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.elevenlabs_voice_id
    
    async def synthesize(self, text: str) -> bytes:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to synthesize
        
        Returns:
            Audio bytes (MP3)
        """
        audio = generate(
            text=text,
            voice=self.voice_id,
            model="eleven_multilingual_v2"
        )
        
        return audio
    
    async def synthesize_to_file(self, text: str, output_path: str) -> str:
        """
        Synthesize and save to file.
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
        
        Returns:
            Path to saved file
        """
        audio = await self.synthesize(text)
        with open(output_path, "wb") as f:
            f.write(audio)
        return output_path
    
    async def stream(self, text: str):
        """
        Stream audio for real-time playback.
        
        Yields:
            Audio chunks
        """
        # For streaming, use the stream method
        audio_stream = elevenlabs.generate(
            text=text,
            voice=self.voice_id,
            model="eleven_multilingual_v2",
            stream=True
        )
        
        for chunk in audio_stream:
            yield chunk


# Singleton instance
_tts_service: Optional[TTSService] = None


def get_tts_service() -> TTSService:
    """Get TTS service instance."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service