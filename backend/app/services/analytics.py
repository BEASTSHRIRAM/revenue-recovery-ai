"""Aggregation queries backing the dashboard and analytics pages.

Plain SQL aggregation, no LLM involved — these are the numbers the whole
product is judged on, so they need to be exactly reproducible from the data.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CaseStatus, MessageStatus
from app.models.message import Message
from app.models.recovery import RecoveryCase


async def overview(session: AsyncSession) -> dict:
    recovered_mrr = await session.scalar(
        select(func.coalesce(func.sum(RecoveryCase.amount_at_risk_cents), 0)).where(
            RecoveryCase.status == CaseStatus.RECOVERED
        )
    )
    at_risk_mrr = await session.scalar(
        select(func.coalesce(func.sum(RecoveryCase.amount_at_risk_cents), 0)).where(
            RecoveryCase.status.notin_([CaseStatus.RECOVERED, CaseStatus.LOST])
        )
    )
    open_cases = await session.scalar(
        select(func.count(RecoveryCase.id)).where(
            RecoveryCase.status.notin_([CaseStatus.RECOVERED, CaseStatus.LOST])
        )
    )
    total_closed = await session.scalar(
        select(func.count(RecoveryCase.id)).where(
            RecoveryCase.status.in_([CaseStatus.RECOVERED, CaseStatus.LOST])
        )
    )
    recovered_closed = await session.scalar(
        select(func.count(RecoveryCase.id)).where(RecoveryCase.status == CaseStatus.RECOVERED)
    )
    avg_days = await session.scalar(
        select(
            func.avg(
                func.julianday(RecoveryCase.closed_at) - func.julianday(RecoveryCase.opened_at)
            )
        ).where(RecoveryCase.status == CaseStatus.RECOVERED)
    )

    recovery_rate = (recovered_closed / total_closed) if total_closed else None
    return {
        "recovered_mrr_cents": int(recovered_mrr or 0),
        "recovery_rate": recovery_rate,
        "at_risk_mrr_cents": int(at_risk_mrr or 0),
        "open_cases": int(open_cases or 0),
        "avg_days_to_recover": float(avg_days) if avg_days is not None else None,
    }


_FUNNEL_ORDER = [
    CaseStatus.OPEN,
    CaseStatus.IN_PROGRESS,
    CaseStatus.AWAITING_CUSTOMER,
    CaseStatus.RECOVERED,
    CaseStatus.LOST,
    CaseStatus.ESCALATED,
]


async def funnel(session: AsyncSession) -> list[dict]:
    rows = (
        await session.execute(
            select(RecoveryCase.status, func.count(RecoveryCase.id)).group_by(RecoveryCase.status)
        )
    ).all()
    counts = {status: count for status, count in rows}
    return [
        {"stage": status.value, "count": counts.get(status, 0)} for status in _FUNNEL_ORDER
    ]


async def by_reason(session: AsyncSession) -> list[dict]:
    rows = (
        await session.execute(
            select(
                RecoveryCase.failure_class,
                func.count(RecoveryCase.id),
                func.sum(case((RecoveryCase.status == CaseStatus.RECOVERED, 1), else_=0)),
                func.coalesce(func.sum(RecoveryCase.amount_at_risk_cents), 0),
            ).group_by(RecoveryCase.failure_class)
        )
    ).all()

    result = []
    for failure_class, total, recovered, amount_at_risk in rows:
        recovered = int(recovered or 0)
        result.append(
            {
                "failure_class": failure_class.value,
                "total_cases": total,
                "recovered_cases": recovered,
                "win_rate": (recovered / total) if total else None,
                "amount_at_risk_cents": int(amount_at_risk),
            }
        )
    return sorted(result, key=lambda r: r["total_cases"], reverse=True)


async def channel_performance(session: AsyncSession) -> list[dict]:
    rows = (
        await session.execute(
            select(
                Message.channel,
                func.sum(case((Message.status == MessageStatus.SENT, 1), else_=0)),
            ).group_by(Message.channel)
        )
    ).all()
    return [
        {
            "channel": channel.value,
            "sent_count": int(sent_count or 0),
            "opened_count": 0,
            "clicked_count": 0,
        }
        for channel, sent_count in rows
    ]


async def trend(session: AsyncSession, days: int = 30) -> list[dict]:
    """Daily recovered vs at-risk amounts over the trailing `days` days."""
    since = datetime.now(UTC) - timedelta(days=days)
    rows = (
        await session.execute(
            select(
                func.date(RecoveryCase.opened_at),
                func.sum(
                    case(
                        (RecoveryCase.status == CaseStatus.RECOVERED, RecoveryCase.amount_at_risk_cents),
                        else_=0,
                    )
                ),
                func.coalesce(func.sum(RecoveryCase.amount_at_risk_cents), 0),
            )
            .where(RecoveryCase.opened_at >= since)
            .group_by(func.date(RecoveryCase.opened_at))
            .order_by(func.date(RecoveryCase.opened_at))
        )
    ).all()
    return [
        {
            "date": date_str,
            "recovered_cents": int(recovered_cents or 0),
            "at_risk_cents": int(at_risk_cents or 0),
        }
        for date_str, recovered_cents, at_risk_cents in rows
    ]
