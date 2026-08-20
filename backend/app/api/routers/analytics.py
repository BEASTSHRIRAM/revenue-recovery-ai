"""Dashboard/analytics endpoints — thin wrappers over app.services.analytics."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.analytics import (
    ByReasonRow,
    ChannelPerformanceRow,
    FunnelStage,
    OverviewStats,
    TrendPoint,
)
from app.services import analytics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewStats)
async def get_overview(session: AsyncSession = Depends(get_session)) -> dict:
    return await analytics.overview(session)


@router.get("/funnel", response_model=list[FunnelStage])
async def get_funnel(session: AsyncSession = Depends(get_session)) -> list[dict]:
    return await analytics.funnel(session)


@router.get("/by-reason", response_model=list[ByReasonRow])
async def get_by_reason(session: AsyncSession = Depends(get_session)) -> list[dict]:
    return await analytics.by_reason(session)


@router.get("/channels", response_model=list[ChannelPerformanceRow])
async def get_channel_performance(session: AsyncSession = Depends(get_session)) -> list[dict]:
    return await analytics.channel_performance(session)


@router.get("/trend", response_model=list[TrendPoint])
async def get_trend(days: int = 30, session: AsyncSession = Depends(get_session)) -> list[dict]:
    return await analytics.trend(session, days=days)
