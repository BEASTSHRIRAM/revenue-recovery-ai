"""End-to-end API contract smoke tests against a real (in-memory) database and
ASGI transport — no mocking of the app itself."""

from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime

import pytest

from app.models.billing import Customer, Invoice, Subscription
from app.models.enums import InvoiceStatus
from app.models.recovery import Playbook, RecoveryCase
from app.providers.mock import MOCK_WEBHOOK_SECRET


async def _seed_one_case(session, failure_class="insufficient_funds") -> str:
    customer = Customer(name="Test Customer", email="test@example.com", mrr_cents=99900, tenure_days=120)
    session.add(customer)
    await session.flush()

    sub = Subscription(customer_id=customer.id, plan_name="Starter", amount_cents=99900)
    session.add(sub)
    await session.flush()

    invoice = Invoice(
        subscription_id=sub.id,
        number="INV-1",
        amount_cents=99900,
        status=InvoiceStatus.PAST_DUE,
        due_at=datetime.now(UTC),
    )
    session.add(invoice)
    await session.flush()

    case = RecoveryCase(
        invoice_id=invoice.id,
        provider="mock",
        provider_payment_id="pay_smoke_001",
        failure_code="BAD001",
        failure_reason="Insufficient balance",
        failure_class=failure_class,
        amount_at_risk_cents=99900,
        opened_at=datetime.now(UTC),
    )
    session.add(case)

    session.add(
        Playbook(
            failure_class=failure_class,
            retry_offsets_hours=[24, 72],
            channel_ladder=["email"],
            offer_policy="test policy",
        )
    )
    await session.commit()
    return case.id


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_capabilities_reports_stub_mode_without_keys(client):
    response = await client.get("/capabilities")
    body = response.json()
    assert body["agent"]["mode"] == "stub"
    assert body["payments"]["effective"] == "mock"


@pytest.mark.asyncio
async def test_case_lifecycle(client, session):
    case_id = await _seed_one_case(session)

    listed = await client.get("/api/cases")
    assert listed.status_code == 200
    assert any(c["id"] == case_id for c in listed.json())

    run = await client.post(f"/api/cases/{case_id}/run")
    assert run.status_code == 200
    body = run.json()
    assert body["case_id"] == case_id
    assert len(body["decisions"]) > 0

    detail = await client.get(f"/api/cases/{case_id}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert len(detail_body["messages"]) >= 1
    assert len(detail_body["agent_steps"]) >= 1


@pytest.mark.asyncio
async def test_run_missing_case_returns_404(client):
    response = await client.post("/api/cases/case_does_not_exist/run")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analytics_overview_returns_shape(client, session):
    await _seed_one_case(session)
    response = await client.get("/api/analytics/overview")
    assert response.status_code == 200
    body = response.json()
    assert "recovered_mrr_cents" in body
    assert "open_cases" in body


@pytest.mark.asyncio
async def test_mock_webhook_requires_valid_signature(client, session):
    await _seed_one_case(session)  # gives the webhook a subscription to attach to
    body = b'{"event": "payment.failed", "payload": {"payment": {"entity": {"id": "pay_x", "amount": 1000}}}}'

    unsigned = await client.post(
        "/api/webhooks/mock", content=body, headers={"Content-Type": "application/json"}
    )
    assert unsigned.status_code == 400

    signature = hmac.new(MOCK_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    signed = await client.post(
        "/api/webhooks/mock",
        content=body,
        headers={"Content-Type": "application/json", "X-Mock-Signature": signature},
    )
    assert signed.status_code == 200
    assert signed.json()["received"] is True
