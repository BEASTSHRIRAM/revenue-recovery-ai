"""Payment provider webhooks: a real Razorpay endpoint plus a mock driver.

Every webhook is verified against the *raw* request body before the JSON is
even parsed for routing — reading `await request.json()` first and verifying
second is the classic way to accidentally trust an unverified payload.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ids import new_id
from app.core.logging import get_logger
from app.db.session import get_session
from app.models.billing import Invoice, Subscription
from app.models.enums import CaseStatus, InvoiceStatus
from app.models.recovery import RecoveryCase
from app.providers import get_payment_provider
from app.providers.mock import MockPaymentProvider
from app.schemas.cases import OutcomeWebhookRequest
from app.services.recovery_service import find_case_by_payment_id, handle_outcome

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
log = get_logger(__name__)


async def _open_case_for_failure(payload: dict, session: AsyncSession) -> RecoveryCase:
    provider = get_payment_provider()
    failure = provider.parse_failure_event(payload)

    # Demo-friendly fallback: reuse any existing customer/subscription/invoice
    # so a webhook fired against seeded data doesn't need a full billing setup
    # dance. A production integration would look these up by the provider's
    # own customer/subscription ids instead.
    subscription = await session.scalar(select(Subscription).limit(1))
    if subscription is None:
        raise HTTPException(status_code=422, detail="no subscription available to attach case to")

    invoice = Invoice(
        subscription_id=subscription.id,
        number=f"INV-WEBHOOK-{new_id('wh')[-6:]}",
        amount_cents=failure.amount_cents or 50000,
        currency=failure.currency,
        status=InvoiceStatus.PAST_DUE,
        due_at=datetime.now(UTC),
    )
    session.add(invoice)
    await session.flush()

    case = RecoveryCase(
        invoice_id=invoice.id,
        provider=provider.name,
        provider_payment_id=failure.provider_payment_id,
        failure_code=failure.failure_code,
        failure_reason=failure.failure_reason,
        amount_at_risk_cents=invoice.amount_cents,
        currency=invoice.currency,
        opened_at=invoice.due_at,
        status=CaseStatus.OPEN,
    )
    session.add(case)
    await session.commit()
    return case


@router.post("/razorpay")
async def razorpay_webhook(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    provider = get_payment_provider()
    if not provider.verify_webhook_signature(raw_body, signature):
        raise HTTPException(status_code=400, detail="invalid webhook signature")

    payload = await request.json()
    event = payload.get("event")

    if event == "payment.failed":
        case = await _open_case_for_failure(payload, session)
        return {"received": True, "case_id": case.id}

    if event == "payment.captured":
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        existing = await find_case_by_payment_id(entity.get("id", ""), session)
        if existing:
            status = await handle_outcome(existing.id, True, session)
            return {"received": True, "case_id": existing.id, "status": status}

    return {"received": True, "ignored_event": event}


@router.post("/mock")
async def mock_webhook(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    """Same shape as the Razorpay webhook, signed with the mock provider's
    fixed dev secret — lets the demo/mock flow be exercised without a real
    gateway or any credentials."""
    raw_body = await request.body()
    signature = request.headers.get("X-Mock-Signature", "")

    mock = MockPaymentProvider()
    if not mock.verify_webhook_signature(raw_body, signature):
        raise HTTPException(status_code=400, detail="invalid mock webhook signature")

    payload = await request.json()
    if payload.get("event") == "payment.failed":
        case = await _open_case_for_failure(payload, session)
        return {"received": True, "case_id": case.id}

    return {"received": True, "ignored_event": payload.get("event")}


@router.post("/outcome")
async def outcome_webhook(
    body: OutcomeWebhookRequest, session: AsyncSession = Depends(get_session)
) -> dict:
    """Convenience endpoint for demos/tests: report an outcome by payment id
    without constructing a full provider-shaped webhook payload."""
    case = await find_case_by_payment_id(body.provider_payment_id, session)
    if case is None:
        raise HTTPException(status_code=404, detail="no case for that provider_payment_id")
    status = await handle_outcome(case.id, body.recovered, session)
    return {"case_id": case.id, "status": status}
