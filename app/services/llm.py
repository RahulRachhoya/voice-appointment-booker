"""LLM service using AWS Bedrock (Anthropic Claude)."""
import json
from typing import Optional, List, Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_aws import ChatBedrock
from app.config import get_settings


# System prompt for the appointment booking agent
APPOINTMENT_BOOKER_SYSTEM = """You are a professional appointment booking assistant for a healthcare clinic / salon / consultancy. 

Your role:
- Answer the phone professionally
- Help customers book, cancel, or reschedule appointments
- Collect necessary information (name, phone, preferred date/time, service type)
- Be friendly but efficient

Guidelines:
- Keep responses short and conversational (1-2 sentences typically)
- Confirm details before finalizing
- If you need to check availability, tell the caller you'll check
- If confused or request is complex, offer to transfer to a human

Services available: Initial consultation, Follow-up visit, Standard appointment, Emergency slot

Today is {current_date}. Available slots: {available_slots}

Remember: You are talking on the phone, so keep responses natural for speech."""


class LLMService:
    """LLM service using Anthropic Claude via AWS Bedrock."""
    
    def __init__(self):
        settings = get_settings()
        
        self.llm = ChatBedrock(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            model_kwargs={
                "max_tokens": 1024,
                "temperature": 0.7,
            },
            credentials_provider=lambda: {
                "aws_access_key_id": settings.aws_access_key_id,
                "aws_secret_access_key": settings.aws_secret_access_key,
                "region_name": settings.aws_region,
            }
        )
        
        self.conversation_history: List[Dict[str, str]] = []
    
    def _build_prompt(self, user_message: str, context: Dict[str, Any]) -> List:
        """Build the prompt with system message and history."""
        # Format available slots
        slots = context.get("available_slots", ["Tomorrow 10am", "Tomorrow 2pm", "Day after 11am"])
        slots_text = ", ".join(slots)
        
        system_msg = SystemMessage(
            content=APPOINTMENT_BOOKER_SYSTEM.format(
                current_date=context.get("current_date", "today"),
                available_slots=slots_text
            )
        )
        
        # Build message history
        messages = [system_msg]
        
        # Add recent conversation (last 6 turns)
        for msg in self.conversation_history[-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=user_message))
        
        return messages
    
    async def generate_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response to the user's message.
        
        Args:
            user_message: The user's speech input
            context: Additional context (available slots, etc.)
        
        Returns:
            Generated response text
        """
        context = context or {}
        
        messages = self._build_prompt(user_message, context)
        
        response = await self.llm.ainvoke(messages)
        
        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        
        return response.content
    
    async def extract_appointment_details(self, text: str) -> Dict[str, Any]:
        """
        Extract appointment details from conversation text.
        
        Returns:
            Dict with keys: name, phone, date, time, service_type
        """
        extraction_prompt = f"""Extract appointment details from this conversation. Return JSON.

Conversation:
{text}

Return exactly this JSON format:
{{
    "customer_name": "extracted name or null",
    "customer_phone": "extracted phone or null", 
    "appointment_date": "extracted date or null",
    "appointment_time": "extracted time or null",
    "service_type": "extracted service or null",
    "confirmed": true/false
}}"""

        messages = [HumanMessage(content=extraction_prompt)]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            # Parse JSON from response
            content = response.content
            # Find JSON in response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
        
        return {"confirmed": False}
    
    def reset_conversation(self):
        """Reset conversation history for a new call."""
        self.conversation_history = []
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation so far."""
        if not self.conversation_history:
            return ""
        
        summary_parts = []
        for msg in self.conversation_history:
            role = "Customer" if msg["role"] == "user" else "Assistant"
            summary_parts.append(f"{role}: {msg['content'][:100]}")
        
        return "\n".join(summary_parts)


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service