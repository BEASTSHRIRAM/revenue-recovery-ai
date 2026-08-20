"""`escalate` — hand a case to a human instead of continuing automation.

Reached for terminal declines (hard_decline, risk_blocked) and cases whose
recovery score is too low to justify further automated effort. No outreach is
sent from here; a human decides what, if anything, happens next.
"""

from __future__ import annotations

import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import RecoveryState
from app.models.enums import CaseStatus
from app.models.recovery import RecoveryCase
from app.db.base import utcnow


async def escalate(state: RecoveryState, session: AsyncSession) -> RecoveryState:
    started = time.monotonic()
    facts = state["facts"]
    failure_class = state["failure_class"]
    recovery_score = state.get("recovery_score")

    case = await session.get(RecoveryCase, facts["case_id"])
    case.status = CaseStatus.ESCALATED
    case.closed_at = utcnow()

    reasoning = (
        f"Escalated to human review: {failure_class.value} "
        f"(score={recovery_score if recovery_score is not None else 'n/a'})."
    )
    latency_ms = int((time.monotonic() - started) * 1000)
    return {
        "decisions": [{"node": "escalate", "reasoning": reasoning, "latency_ms": latency_ms}],
    }
