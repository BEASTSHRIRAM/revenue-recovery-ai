"""`ingest` — deterministic DB load, no LLM involved.

Every fact the rest of the graph reasons over comes from this node. The
guardrail node later checks that composed message copy doesn't state any
number that isn't traceable back to `state["facts"]`, so this is the one place
allowed to read raw amounts/dates out of the database.
"""

from __future__ import annotations

import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import RecoveryState
from app.models.billing import Customer, Invoice, Subscription
from app.models.recovery import RecoveryCase


async def ingest(state: RecoveryState, session: AsyncSession) -> RecoveryState:
    started = time.monotonic()
    case_id = state["case_id"]

    case = await session.get(RecoveryCase, case_id)
    if case is None:
        raise ValueError(f"RecoveryCase {case_id} not found")

    invoice = await session.get(Invoice, case.invoice_id)
    subscription = await session.get(Subscription, invoice.subscription_id)
    customer = await session.get(Customer, subscription.customer_id)

    facts = {
        "case_id": case.id,
        "invoice_id": invoice.id,
        "invoice_number": invoice.number,
        "amount_cents": case.amount_at_risk_cents,
        "currency": case.currency,
        "failure_code": case.failure_code,
        "failure_reason": case.failure_reason,
        "attempt_count": case.attempt_count,
        "customer_id": customer.id,
        "customer_name": customer.name,
        "customer_email": customer.email,
        "customer_phone": customer.phone,
        "customer_tenure_days": customer.tenure_days,
        "plan_name": subscription.plan_name,
    }

    latency_ms = int((time.monotonic() - started) * 1000)
    return {
        "facts": facts,
        "decisions": [
            {
                "node": "ingest",
                "reasoning": f"Loaded case for {customer.name}: "
                f"{facts['amount_cents'] / 100:.2f} {facts['currency']} at risk, "
                f"failure code {facts['failure_code']}.",
                "latency_ms": latency_ms,
            }
        ],
    }
