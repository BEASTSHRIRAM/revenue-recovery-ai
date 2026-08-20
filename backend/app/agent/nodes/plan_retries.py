"""`plan_retries` — choose retry timing and channel ladder, no LLM.

Pulls the matching Playbook's retry offsets and channel ladder. This is
deliberately rule-based: retry *timing* is a policy decision (payday-aligned
for insufficient funds, fast for transient technical errors, none at all for
anything needing customer action) that should be edited on the Playbooks page,
not re-derived by a model on every run.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import RecoveryState
from app.models.recovery import Playbook


async def plan_retries(state: RecoveryState, session: AsyncSession) -> RecoveryState:
    started = time.monotonic()
    failure_class = state["failure_class"]

    playbook = await session.scalar(
        select(Playbook).where(Playbook.failure_class == failure_class)
    )
    offsets = playbook.retry_offsets_hours if playbook else []
    channels = playbook.channel_ladder if playbook else ["email"]
    offer_policy = playbook.offer_policy if playbook else None

    now = datetime.now(UTC)
    retry_schedule = [
        {"offset_hours": h, "scheduled_at": (now + timedelta(hours=h)).isoformat()}
        for h in offsets
    ]

    strategy = {
        "retry_schedule": retry_schedule,
        "channel_ladder": channels,
        "offer_policy": offer_policy,
        "requires_customer_action": False,
    }

    latency_ms = int((time.monotonic() - started) * 1000)
    reasoning = (
        f"{len(offsets)} retries at +{offsets}h via {failure_class.value} playbook, "
        f"outreach over {channels}."
        if offsets
        else f"No retry offsets configured for {failure_class.value}; outreach only over {channels}."
    )
    return {
        "strategy": strategy,
        "next_action": "compose",
        "decisions": [
            {"node": "plan_retries", "reasoning": reasoning, "latency_ms": latency_ms, "output": strategy}
        ],
    }
