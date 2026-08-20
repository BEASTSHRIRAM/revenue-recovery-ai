"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import agent, analytics, cases, playbooks, system, webhooks
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.db.session import init_models

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
        "groq" if settings.groq_enabled else "stub",
        settings.effective_payment_provider,
        settings.effective_email_channel,
    )
    if settings.is_sqlite:
        # Dev convenience: create tables if they don't exist yet, so booting
        # the server against a fresh/relocated SQLite file never 500s with
        # "no such table" just because `python -m app.db.seed` wasn't run
        # first from the exact same working directory. Postgres deployments
        # use `alembic upgrade head` instead — see init_models()'s docstring.
        await init_models()
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
    app.include_router(cases.router)
    app.include_router(playbooks.router)
    app.include_router(analytics.router)
    app.include_router(webhooks.router)
    app.include_router(agent.router)

    return app


app = create_app()
