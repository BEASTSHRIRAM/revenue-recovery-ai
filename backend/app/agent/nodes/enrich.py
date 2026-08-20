"""`enrich` — deterministic feature engineering, no LLM.

Kept as a separate node (rather than folded into `score`) so the numeric
features are visible in the decision trace on their own, before any model
judgment is layered on top.
"""

from __future__ import annotations

import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import RecoveryState
from app.models.billing import Customer
from app.models.recovery import RecoveryCase
from app.services.features import build_features


async def enrich(state: RecoveryState, session: AsyncSession) -> RecoveryState:
    started = time.monotonic()
    facts = state["facts"]

    case = await session.get(RecoveryCase, facts["case_id"])
    customer = await session.get(Customer, facts["customer_id"])
    features = build_features(customer, case, state["failure_class"])

    latency_ms = int((time.monotonic() - started) * 1000)
    return {
        "features": features,
        "decisions": [
            {
                "node": "enrich",
                "reasoning": (
                    f"historical_recovery_rate={features['historical_recovery_rate']:.2f}, "
                    f"tenure_days={int(features['tenure_days'])}, "
                    f"attempts_used={int(features['attempts_used'])}."
                ),
                "latency_ms": latency_ms,
                "output": features,
            }
        ],
    }
