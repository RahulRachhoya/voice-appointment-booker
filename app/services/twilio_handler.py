"""Twilio webhook handler for incoming calls."""
import os
import tempfile
from typing import Optional
from twilio.rest import Client
from twilio.twiml import VoiceResponse
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import Response

router = APIRouter()


class TwilioHandler:
    """Handles Twilio webhook interactions."""
    
    def __init__(self):
        from app.config import get_settings
        settings = get_settings()
        
        self.client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.phone_number = settings.twilio_phone_number
    
    async def handle_incoming_call(self, request: Request) -> Response:
        """
        Handle incoming Twilio voice call.
        
        Returns TwiML to:
        1. Greet the caller
        2. Start recording
        3. Stream to our server for processing
        """
        # Get call details
        call_sid = request.form.get("CallSid", "")
        caller_number = request.form.get("From", "")
        
        # For demo: simple greeting via TwiML
        # In production: stream audio to FastAPI endpoint
        response = VoiceResponse()
        
        # Greet the caller
        response.say(
            "Hello! Thank you for calling. Please hold while I connect you to our AI assistant.",
            voice="Polly.Joanna-Neural"
        )
        
        # Start record for transcription
        response.record(
            max_length=300,
            timeout=10,
            transcribe_callback=f"/webhooks/twilio/transcription?call_sid={call_sid}"
        )
        
        # If they hang up
        response.hangup()
        
        return Response(content=str(response), media_type="application/xml")
    
    async def handle_recording_complete(self, call_sid: str, recording_url: str) -> dict:
        """
        Handle completed recording.
        
        Would trigger:
        1. Download recording
        2. Transcribe with STT
        3. Process with LLM
        4. Generate TTS response
        5. Make outbound call with response
        
        For now, return recording info.
        """
        return {
            "status": "recording_complete",
            "call_sid": call_sid,
            "recording_url": recording_url
        }
    
    async def make_outbound_call(
        self,
        to_number: str,
        twiml_message: str
    ) -> dict:
        """
        Make an outbound call with TwiML message.
        
        Args:
            to_number: Phone number to call
            twiml_message: Message to say
        
        Returns:
            Call object
        """
        call = self.client.calls.create(
            twiml=f"<Response><Say>{twiml_message}</Say></Response>",
            to=to_number,
            from_=self.phone_number
        )
        
        return {
            "call_sid": call.sid,
            "status": call.status
        }
    
    async def play_message(self, call_sid: str, audio_url: str) -> dict:
        """
        Play an audio file to an active call.
        
        Args:
            call_sid: The active call's SID
            audio_url: URL to the audio file
        
        Returns:
            Status dict
        """
        call = self.client.calls(call_sid).update(
            method="POST",
            url=audio_url
        )
        
        return {"status": "playing", "call_sid": call.sid}
    
    async def end_call(self, call_sid: str) -> dict:
        """End an active call."""
        self.client.calls(call_sid).update(status="completed")
        return {"status": "ended", "call_sid": call_sid}


# Singleton
_twilio_handler: Optional[TwilioHandler] = None


def get_twilio_handler() -> TwilioHandler:
    """Get Twilio handler instance."""
    global _twilio_handler
    if _twilio_handler is None:
        _twilio_handler = TwilioHandler()
    return _twilio_handler