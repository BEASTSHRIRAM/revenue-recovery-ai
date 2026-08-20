"""`evaluate` — re-entered when a payment webhook reports an outcome.

Not part of the initial graph path; `RecoveryService.handle_outcome()` invokes
this directly against a case's checkpointed state. Closes the case on success,
escalates once retries are exhausted, otherwise leaves it open for the next
scheduled attempt. Also updates the matching Playbook's live win-rate counters
so the Playbooks page reflects real outcomes.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.db.base import utcnow
from app.models.enums import CaseStatus
from app.models.recovery import Playbook, RecoveryCase

log = get_logger(__name__)


async def evaluate_outcome(case: RecoveryCase, recovered: bool, session: AsyncSession) -> str:
    """Update a case (and its playbook) after a retry or customer action resolves it.

    Returns the new CaseStatus value as a string for the caller to report back.
    """
    if recovered:
        case.status = CaseStatus.RECOVERED
        case.closed_at = utcnow()
    elif case.attempt_count >= settings.max_retries_per_case:
        case.status = CaseStatus.LOST
        case.closed_at = utcnow()
    else:
        case.status = CaseStatus.IN_PROGRESS
        # Left open — the scheduled retry worker or another outreach step will
        # pick this case back up; nothing further to do here.

    if case.status.is_closed:
        playbook = await session.scalar(
            select(Playbook).where(Playbook.failure_class == case.failure_class)
        )
        if playbook:
            playbook.cases_closed += 1
            if recovered:
                playbook.cases_recovered += 1
            log.info(
                "playbook updated  failure_class=%s  win_rate=%.2f",
                case.failure_class.value,
                playbook.win_rate or 0.0,
            )

    return case.status.value
