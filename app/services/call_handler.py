"""Call handler orchestrating the voice AI pipeline."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.services.stt import get_stt_service
from app.services.llm import get_llm_service
from app.services.tts import get_tts_service
from app.models import Call, Appointment


class CallHandler:
    """
    Orchestrates the full voice pipeline:
    Phone → STT → LLM → TTS → Phone
    """
    
    def __init__(self):
        self.stt = get_stt_service()
        self.llm = get_llm_service()
        self.tts = get_tts_service()
        
        # Call state
        self.current_call: Optional[Call] = None
        self.call_sid: Optional[str] = None
    
    async def init_call(self, call_sid: str, caller_number: str) -> Call:
        """Initialize a new call."""
        self.call_sid = call_sid
        self.llm.reset_conversation()
        
        # Create call record
        self.current_call = Call(
            call_sid=call_sid,
            caller_number=caller_number,
            status="initiated"
        )
        
        return self.current_call
    
    async def handle_incoming_audio(self, audio_bytes: bytes) -> bytes:
        """
        Handle incoming audio: STT → LLM → TTS → Return audio response.
        
        Args:
            audio_bytes: Raw audio from caller
         Returns:
            Audio bytes to play back to caller
        """
        if not self.current_call:
            raise RuntimeError("Call not initialized. Call init_call first.")
        
        # Step 1: Speech to Text
        user_text = await self.stt.transcribe(audio_bytes)
        
        if not user_text.strip():
            # No speech detected, play prompt
            return await self._generate_prompt_response("I didn't catch that. Could you please repeat?")
        
        # Step 2: Generate LLM response
        context = self._build_context()
        llm_response = await self.llm.generate_response(user_text, context)
        
        # Step 3: Text to Speech
        audio_response = await self.tts.synthesize(llm_response)
        
        return audio_response
    
    async def _generate_prompt_response(self, text: str) -> bytes:
        """Convert text to speech for prompts."""
        return await self.tts.synthesize(text)
    
    def _build_context(self) -> Dict[str, Any]:
        """Build context for LLM."""
        # Get available slots (would come from calendar in production)
        available_slots = self._get_available_slots()
        
        return {
            "current_date": datetime.now().strftime("%B %d, %Y"),
            "available_slots": available_slots,
            "call_sid": self.call_sid,
        }
    
    def _get_available_slots(self) -> list:
        """Get available appointment slots."""
        # In production, this would query Google Calendar
        today = datetime.now()
        return [
            f"Today {(today + timedelta(hours=i)).strftime('%I:%M %p')}" 
            for i in range(2, 6, 2)
        ] + [
            f"Tomorrow {(today + timedelta(days=1, hours=h)).strftime('%I:%M %p')}"
            for h in [10, 14, 16]
        ]
    
    async def handle_greeting(self) -> bytes:
        """Generate greeting for incoming call."""
        greeting = (
            "Hello! Thank you for calling. I'm your appointment assistant. "
            "I can help you book, cancel, or reschedule an appointment. "
            "How may I help you today?"
        )
        return await self._generate_prompt_response(greeting)
    
    async def handle_end_call(self) -> Dict[str, Any]:
        """Process call ending, extract details, create appointment."""
        if not self.current_call:
            return {"status": "no_call"}
        
        # Get conversation summary
        summary = self.llm.get_conversation_summary()
        self.current_call.summary = summary
        self.current_call.status = "completed"
        
        # Try to extract appointment details
        details = await self.llm.extract_appointment_details(summary)
        
        if details.get("confirmed") and details.get("appointment_date"):
            # Create appointment
            appointment = Appointment(
                call_id=self.current_call.id,
                customer_name=details.get("customer_name"),
                customer_phone=details.get("customer_phone"),
                appointment_date=datetime.fromisoformat(details["appointment_date"]),
                service_type=details.get("service_type", "Standard"),
                status="pending"
            )
            self.current_call.appointment_booked = True
            
            return {
                "status": "appointment_booked",
                "appointment": appointment,
                "summary": summary
            }
        
        return {
            "status": "completed",
            "summary": summary,
            "appointment_booked": False
        }
    
    def should_escalate_to_human(self) -> bool:
        """
        Determine if call should be escalated to human.
        
        Checks:
        - Too many turns without resolution
        - Explicit request for human
        - Complex/unclear intent
        """
        if not self.current_call:
            return False
        
        # Escalate after 10 turns without booking
        if self.current_call.turn_count > 10:
            return True
        
        # Check for escalation keywords in recent conversation
        recent = self.llm.conversation_history[-2:] if self.llm.conversation_history else []
        escalation_keywords = ["speak to a person", "talk to human", "manager", "supervisor"]
        
        for msg in recent:
            if msg["role"] == "user":
                if any(kw in msg["content"].lower() for kw in escalation_keywords):
                    return True
        
        return False


# Singleton instance
_call_handler: Optional[CallHandler] = None


def get_call_handler() -> CallHandler:
    """Get call handler instance."""
    global _call_handler
    if _call_handler is None:
        _call_handler = CallHandler()
    return _call_handler