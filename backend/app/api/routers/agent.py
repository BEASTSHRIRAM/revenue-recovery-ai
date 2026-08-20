"""SSE endpoint streaming the agent's decision trace live as a case runs."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services.recovery_service import stream_case

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.get("/cases/{case_id}/stream")
async def stream_case_run(
    case_id: str, session: AsyncSession = Depends(get_session)
) -> StreamingResponse:
    async def event_source():
        async for decision in stream_case(case_id, session):
            yield f"data: {json.dumps(decision)}\n\n"
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")
