"""LLM service using Groq Llama-3.3-70b-versatile."""

import logging
from typing import Any

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a professional appointment booking assistant for a healthcare clinic.

Your role:
- Greet callers warmly and help them book, cancel, or reschedule appointments.
- Collect required info: customer name, preferred date, preferred time, and service type.
- Confirm details before finalising.
- Keep responses short and conversational (1-3 sentences), suitable for speech.

Services available: Initial consultation, Follow-up visit, Standard appointment, Emergency slot.

Available time slots: Monday-Friday 9am-5pm, Saturday 10am-2pm.
If a caller asks for an unavailable slot, offer the nearest alternative.

Always be polite and professional. Never ask for sensitive payment info.
"""


async def respond(transcript: str, history: list[dict[str, Any]]) -> str:
    """Generate a booking-agent reply using Groq Llama-3.3-70b-versatile.

    Args:
        transcript: Latest user utterance.
        history: Conversation history as list of {"role": ..., "content": ...} dicts.

    Returns:
        Assistant reply string.

    Raises:
        RuntimeError: If the LLM call fails.
    """
    try:
        import groq  # type: ignore[import-untyped]

        from voice_agent.config import get_settings

        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set")

        client = groq.AsyncGroq(api_key=settings.groq_api_key)

        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in history[-10:]:  # keep last 10 turns for context
            messages.append({"role": str(turn["role"]), "content": str(turn["content"])})
        messages.append({"role": "user", "content": transcript})

        completion = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,  # type: ignore[arg-type]
            max_tokens=256,
            temperature=0.7,
        )

        reply = completion.choices[0].message.content or ""
        log.info("LLM responded with %d chars", len(reply))
        return reply.strip()

    except Exception as exc:
        log.error("LLM call failed: %s", exc)
        raise RuntimeError(f"LLM failed: {exc}") from exc
