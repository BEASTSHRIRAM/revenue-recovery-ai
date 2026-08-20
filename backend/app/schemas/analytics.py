"""API schemas for dashboard/analytics endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class OverviewStats(BaseModel):
    recovered_mrr_cents: int
    recovery_rate: float | None
    at_risk_mrr_cents: int
    open_cases: int
    avg_days_to_recover: float | None


class FunnelStage(BaseModel):
    stage: str
    count: int


class ByReasonRow(BaseModel):
    failure_class: str
    total_cases: int
    recovered_cases: int
    win_rate: float | None
    amount_at_risk_cents: int


class ChannelPerformanceRow(BaseModel):
    channel: str
    sent_count: int
    # Placeholder for future open/click tracking; kept explicit rather than
    # omitted so the frontend contract doesn't need to change when it lands.
    opened_count: int
    clicked_count: int


class TrendPoint(BaseModel):
    date: str
    recovered_cents: int
    at_risk_cents: int
