"""Health and capability introspection.

`/health` is the liveness probe. `/capabilities` reports which subsystems are
running for real versus degraded to a local fallback — the frontend Settings page
renders this directly, so an operator can see at a glance whether Grok is wired
up, whether emails will actually send, and which payment provider is live.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


@router.get("/capabilities")
async def capabilities() -> dict[str, object]:
    """What is live and what is degraded, with a reason for each degradation."""
    return {
        "agent": {
            "provider": "xai",
            "model": settings.grok_model,
            "live": settings.grok_enabled,
            "mode": "grok" if settings.grok_enabled else "stub",
            "note": None
            if settings.grok_enabled
            else "XAI_API_KEY not set — agent is running deterministic stub reasoning.",
        },
        "payments": {
            "configured": settings.payment_provider,
            "effective": settings.effective_payment_provider,
            "live": settings.effective_payment_provider == "razorpay",
            "note": None
            if settings.effective_payment_provider == settings.payment_provider
            else "Razorpay credentials missing — using the mock provider.",
        },
        "email": {
            "configured": settings.email_channel,
            "effective": settings.effective_email_channel,
            "live": settings.effective_email_channel != "simulated",
            "note": None
            if settings.effective_email_channel == settings.email_channel
            else "Sender not configured — messages queue to the simulated outbox.",
        },
        "database": {
            "engine": "sqlite" if settings.is_sqlite else "postgres",
        },
        "guardrails": {
            "max_messages_per_customer_per_week": settings.max_messages_per_customer_per_week,
            "max_retries_per_case": settings.max_retries_per_case,
            "require_human_approval": settings.require_human_approval,
        },
    }
