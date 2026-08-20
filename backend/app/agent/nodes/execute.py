"""`execute` — persist the plan and hand approved messages to their senders.

Writes RecoveryAttempt rows for the retry schedule, and Message rows for every
draft (approved or blocked — a blocked draft still needs to be visible in the
UI for human review, just not sent). Only messages the guardrail approved
actually get handed to a ChannelSender.
"""

from __future__ import annotations

import time
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import RecoveryState
from app.channels import get_channel_sender
from app.core.config import settings
from app.models.enums import AttemptKind, AttemptOutcome, CaseStatus, MessageStatus
from app.models.message import Message
from app.models.recovery import RecoveryAttempt, RecoveryCase

_MODEL_LABEL = settings.groq_model if settings.groq_enabled else "stub"


async def execute(state: RecoveryState, session: AsyncSession) -> RecoveryState:
    started = time.monotonic()
    facts = state["facts"]
    strategy = state["strategy"]
    drafts = state.get("drafts", [])
    approved = state.get("approved_drafts", [])
    flags = state.get("guardrail_flags", [])
    case_id = facts["case_id"]

    approved_channels = {d["channel"] for d in approved}

    for entry in strategy.get("retry_schedule", []):
        session.add(
            RecoveryAttempt(
                case_id=case_id,
                kind=AttemptKind.RETRY_CHARGE,
                scheduled_at=datetime.fromisoformat(entry["scheduled_at"]),
                outcome=AttemptOutcome.SCHEDULED,
            )
        )

    sent_count = 0
    for draft in drafts:
        is_approved = draft["channel"] in approved_channels
        message = Message(
            case_id=case_id,
            channel=draft["channel"],
            subject=draft.get("subject"),
            body=draft["body"],
            generated_by=_MODEL_LABEL,
            guardrail_flags=[f for f in flags if f.startswith(f"{draft['channel']}:")] or None,
            status=MessageStatus.APPROVED if is_approved else MessageStatus.BLOCKED,
        )
        session.add(message)
        await session.flush()

        session.add(
            RecoveryAttempt(
                case_id=case_id,
                kind=AttemptKind.OUTREACH,
                scheduled_at=message.created_at,
                outcome=AttemptOutcome.SCHEDULED if is_approved else AttemptOutcome.SKIPPED,
            )
        )

        if is_approved:
            sender = get_channel_sender(draft["channel"])
            to = facts["customer_email"] if draft["channel"] == "email" else facts["customer_phone"]
            if to:
                result = await sender.send(
                    to, draft.get("subject"), draft["body"], case_id=case_id
                )
                message.status = MessageStatus.SENT if result.succeeded else MessageStatus.FAILED
                message.provider_message_id = result.provider_message_id
                message.sent_at = message.created_at if result.succeeded else None
                if result.succeeded:
                    sent_count += 1

    case = await session.get(RecoveryCase, case_id)
    case.status = (
        CaseStatus.AWAITING_CUSTOMER if strategy.get("requires_customer_action") else CaseStatus.IN_PROGRESS
    )
    case.strategy = strategy

    latency_ms = int((time.monotonic() - started) * 1000)
    return {
        "decisions": [
            {
                "node": "execute",
                "reasoning": (
                    f"Scheduled {len(strategy.get('retry_schedule', []))} retry attempt(s), "
                    f"sent {sent_count}/{len(drafts)} message(s)."
                ),
                "latency_ms": latency_ms,
            }
        ],
    }
