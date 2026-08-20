"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import system
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

log = get_logger(__name__)

DESCRIPTION = """
AI-driven recovery of failed subscription payments.

Each failed charge becomes a **recovery case** that a LangGraph agent works:
triage the decline reason, score recoverability, choose retry timing and
outreach channels, draft the customer message, and verify it before it sends.
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log.info("starting revenue-recovery-ai  env=%s", settings.app_env)
    log.info(
        "capabilities  agent=%s  payments=%s  email=%s",
        "grok" if settings.grok_enabled else "stub",
        settings.effective_payment_provider,
        settings.effective_email_channel,
    )
    yield
    log.info("shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Revenue Recovery AI",
        description=DESCRIPTION,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(system.router)

    return app


app = create_app()
