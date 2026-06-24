"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from voice_agent.api.routes import appointments, chat, health


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup + shutdown."""
    import logging

    logging.basicConfig(level="INFO", format="%(levelname)s %(name)s: %(message)s")
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI app."""
    application = FastAPI(
        title="Voice AI Appointment Booker",
        description="AI-powered voice agent for appointment booking using Groq + ElevenLabs",
        version="1.0.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000", "http://localhost:7860"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )

    application.include_router(health.router)
    application.include_router(chat.router, prefix="/api")
    application.include_router(appointments.router, prefix="/api")

    @application.get("/")
    async def root() -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
        return {"name": "Voice AI Appointment Booker", "status": "running", "version": "1.0.0"}

    return application


app = create_app()
