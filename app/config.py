"""Configuration loader for Voice AI Appointment Booker."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    
    # OpenAI
    openai_api_key: str = ""
    
    # AWS Bedrock (primary LLM)
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-south-1"
    
    # ElevenLabs (TTS)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    
    # Database
    database_url: str = "sqlite:///./voice_booker.db"
    
    # Google Calendar
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # App Config
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()