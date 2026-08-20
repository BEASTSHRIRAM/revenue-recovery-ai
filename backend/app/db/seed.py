"""Populate a fresh database with realistic demo data.

Run with `python -m app.db.seed`. Idempotent-ish: it wipes and recreates tables
via `init_models()` rather than trying to upsert, since this is a demo/dev
fixture, not production data. Every FailureClass gets representation so the
dashboard, funnel, and playbooks all render meaningfully on first run.
"""

from __future__ import annotations

import asyncio
import random
from datetime import UTC, datetime, timedelta

from app.db.session import SessionLocal, init_models
from app.models import Customer, Invoice, Playbook, RecoveryAttempt, RecoveryCase, Subscription
from app.models.enums import AttemptKind, AttemptOutcome, CaseStatus, FailureClass, InvoiceStatus

random.seed(42)  # reproducible demo data across runs

PLANS = [
    ("Starter", 99900),
    ("Growth", 299900),
    ("Scale", 799900),
]

FIRST_NAMES = [
    "Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Neha", "Arjun", "Kavya",
    "Sanjay", "Meera", "Karan", "Isha", "Rahul", "Divya", "Amit", "Sneha",
    "Nikhil", "Pooja", "Varun", "Riya",
]
LAST_NAMES = [
    "Sharma", "Patel", "Reddy", "Nair", "Gupta", "Iyer", "Kumar", "Menon",
    "Rao", "Verma", "Joshi", "Desai", "Malhotra", "Chatterjee", "Pillai",
]

# (failure_class, raw code, raw description, weight) — weights roughly mirror
# real-world dunning distributions where insufficient funds dominates.
FAILURE_PROFILES: list[tuple[FailureClass, str, str, int]] = [
    (FailureClass.INSUFFICIENT_FUNDS, "BAD001", "Insufficient balance in the account.", 35),
    (FailureClass.CARD_EXPIRED, "BAD002", "The card has expired.", 15),
    (FailureClass.CARD_INVALID, "BAD003", "The card details entered are invalid.", 8),
    (FailureClass.DO_NOT_HONOR, "GEN001", "Issuing bank declined the transaction.", 15),
    (FailureClass.AUTHENTICATION_REQUIRED, "BAD005", "3-D Secure authentication was not completed.", 10),
    (FailureClass.RISK_BLOCKED, "SEC001", "Transaction flagged by risk engine.", 5),
    (FailureClass.TECHNICAL_ERROR, "GTW001", "Gateway timeout while processing the payment.", 7),
    (FailureClass.HARD_DECLINE, "BAD009", "Do not honor - contact card issuer.", 5),
]

DEFAULT_PLAYBOOKS: dict[FailureClass, tuple[list[int], list[str], str]] = {
    FailureClass.INSUFFICIENT_FUNDS: ([72, 168, 336], ["email", "sms"], "Payday-aligned retries, no discounts."),
    FailureClass.CARD_EXPIRED: ([], ["email", "sms"], "No retry - request a card update, single reminder."),
    FailureClass.CARD_INVALID: ([], ["email"], "No retry - request corrected card details."),
    FailureClass.DO_NOT_HONOR: ([24, 96], ["email"], "Two spaced retries, gentle outreach."),
    FailureClass.AUTHENTICATION_REQUIRED: ([], ["email", "sms"], "No retry - request 3DS re-authentication."),
    FailureClass.RISK_BLOCKED: ([], ["email"], "No retry - escalate to support, no automated messaging."),
    FailureClass.TECHNICAL_ERROR: ([1, 6, 24], ["email"], "Fast retries - likely transient."),
    FailureClass.HARD_DECLINE: ([], ["email"], "No retry - escalate, suggest alternate payment method."),
    FailureClass.UNKNOWN: ([24], ["email"], "Single cautious retry pending triage."),
}


def _weighted_choice() -> tuple[FailureClass, str, str]:
    chosen = random.choices(FAILURE_PROFILES, weights=[p[3] for p in FAILURE_PROFILES])[0]
    return chosen[0], chosen[1], chosen[2]


async def seed(num_customers: int = 60, num_cases: int = 120) -> None:
    await init_models()
    now = datetime.now(UTC)

    async with SessionLocal() as session:
        # ---------- playbooks ----------
        for failure_class, (offsets, channels, policy) in DEFAULT_PLAYBOOKS.items():
            session.add(
                Playbook(
                    failure_class=failure_class,
                    retry_offsets_hours=offsets,
                    channel_ladder=channels,
                    offer_policy=policy,
                    cases_closed=random.randint(20, 80),
                    cases_recovered=0,
                )
            )
        await session.flush()

        # ---------- customers + subscriptions ----------
        customers: list[Customer] = []
        for i in range(num_customers):
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            plan_name, amount_cents = random.choice(PLANS)
            tenure_days = random.randint(15, 900)
            failed = random.randint(0, 6)
            recovered = random.randint(0, failed) if failed else 0

            customer = Customer(
                external_id=f"cust_demo_{i:04d}",
                name=name,
                email=f"{name.lower().replace(' ', '.')}{i}@example.com",
                phone=f"+9198{random.randint(10000000, 99999999)}",
                mrr_cents=amount_cents,
                tenure_days=tenure_days,
                lifetime_failed_count=failed,
                lifetime_recovered_count=recovered,
                lifetime_recovered_cents=recovered * amount_cents,
            )
            session.add(customer)
            customers.append(customer)
        await session.flush()

        subscriptions: list[Subscription] = []
        for customer in customers:
            plan_name, amount_cents = random.choice(PLANS)
            sub = Subscription(
                external_id=f"sub_{customer.external_id}",
                customer_id=customer.id,
                plan_name=plan_name,
                amount_cents=amount_cents,
                next_billing_at=now + timedelta(days=random.randint(1, 30)),
                started_at=now - timedelta(days=customer.tenure_days),
            )
            session.add(sub)
            subscriptions.append(sub)
        await session.flush()

        # ---------- invoices + recovery cases ----------
        recovered_by_class: dict[FailureClass, int] = {}
        closed_by_class: dict[FailureClass, int] = {}

        for i in range(num_cases):
            sub = random.choice(subscriptions)
            failure_class, code, reason = _weighted_choice()
            days_ago = random.randint(0, 45)
            opened_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))

            invoice = Invoice(
                external_id=f"inv_demo_{i:04d}",
                subscription_id=sub.id,
                number=f"INV-{2000 + i}",
                amount_cents=sub.amount_cents,
                status=InvoiceStatus.PAST_DUE,
                due_at=opened_at,
            )
            session.add(invoice)
            await session.flush()

            # Resolve most older cases so the funnel/analytics have real closed
            # outcomes to show, while recent cases stay open/in-progress.
            if days_ago > 5:
                is_retryable = failure_class.is_retryable
                recovers = is_retryable and random.random() < 0.62
                status = CaseStatus.RECOVERED if recovers else (
                    CaseStatus.LOST if random.random() < 0.7 else CaseStatus.ESCALATED
                )
                closed_at = opened_at + timedelta(days=random.randint(1, 6))
                attempt_count = random.randint(1, 4)
                recovery_score = round(random.uniform(0.55, 0.9), 2) if recovers else round(
                    random.uniform(0.05, 0.4), 2
                )
            else:
                status = random.choice(
                    [CaseStatus.OPEN, CaseStatus.IN_PROGRESS, CaseStatus.AWAITING_CUSTOMER]
                )
                closed_at = None
                attempt_count = random.randint(0, 2)
                recovery_score = round(random.uniform(0.3, 0.85), 2)

            case = RecoveryCase(
                invoice_id=invoice.id,
                provider="mock",
                provider_payment_id=f"pay_demo_{i:04d}",
                failure_code=code,
                failure_reason=reason,
                failure_class=failure_class,
                triage_rationale=f"Classified from gateway code {code}: {reason.lower()}",
                recovery_score=recovery_score,
                score_confidence=round(random.uniform(0.6, 0.95), 2),
                status=status,
                amount_at_risk_cents=invoice.amount_cents,
                attempt_count=attempt_count,
                opened_at=opened_at,
                closed_at=closed_at,
            )
            session.add(case)
            await session.flush()

            for a in range(attempt_count):
                kind = AttemptKind.RETRY_CHARGE if failure_class.is_retryable else AttemptKind.OUTREACH
                outcome = (
                    AttemptOutcome.SUCCEEDED
                    if status == CaseStatus.RECOVERED and a == attempt_count - 1
                    else AttemptOutcome.FAILED
                    if kind == AttemptKind.RETRY_CHARGE
                    else AttemptOutcome.SCHEDULED
                )
                session.add(
                    RecoveryAttempt(
                        case_id=case.id,
                        kind=kind,
                        scheduled_at=opened_at + timedelta(hours=24 * (a + 1)),
                        executed_at=opened_at + timedelta(hours=24 * (a + 1)) if closed_at else None,
                        outcome=outcome,
                    )
                )

            if status.is_closed:
                closed_by_class[failure_class] = closed_by_class.get(failure_class, 0) + 1
                if status == CaseStatus.RECOVERED:
                    recovered_by_class[failure_class] = recovered_by_class.get(failure_class, 0) + 1

        await session.commit()
        print(f"seeded {num_customers} customers, {num_cases} recovery cases, "
              f"{len(DEFAULT_PLAYBOOKS)} playbooks")


if __name__ == "__main__":
    asyncio.run(seed())
