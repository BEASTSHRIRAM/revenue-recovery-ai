"""`plan_action_required` — strategy for failures needing customer action.

Card expired/invalid and 3DS-auth-required failures share a shape: retrying
the same instrument is wasted effort, so the only strategy is outreach asking
the customer to act (update card, re-authenticate). Kept separate from
`plan_retries` so that "no retry" is structural, not a zero-length list that
looks like a bug.
"""

from __future__ import annotations

import time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import RecoveryState
from app.models.recovery import Playbook


async def plan_action_required(state: RecoveryState, session: AsyncSession) -> RecoveryState:
    started = time.monotonic()
    failure_class = state["failure_class"]

    playbook = await session.scalar(
        select(Playbook).where(Playbook.failure_class == failure_class)
    )
    channels = playbook.channel_ladder if playbook else ["email"]
    offer_policy = playbook.offer_policy if playbook else None

    strategy = {
        "retry_schedule": [],
        "channel_ladder": channels,
        "offer_policy": offer_policy,
        "requires_customer_action": True,
    }

    latency_ms = int((time.monotonic() - started) * 1000)
    return {
        "strategy": strategy,
        "next_action": "compose",
        "decisions": [
            {
                "node": "plan_action_required",
                "reasoning": (
                    f"{failure_class.value} requires customer action, not a retry; "
                    f"outreach over {channels}."
                ),
                "latency_ms": latency_ms,
                "output": strategy,
            }
        ],
    }
