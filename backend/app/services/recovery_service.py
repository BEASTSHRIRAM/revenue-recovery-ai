"""Orchestrates running the recovery graph for a case and handling outcomes.

This is the seam between the API layer and the LangGraph agent: routers never
touch `build_graph` or a checkpointer directly, they call `run_case` /
`handle_outcome` / `stream_case` here.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.graph import build_graph
from app.agent.nodes.evaluate import evaluate_outcome
from app.core.config import settings
from app.core.logging import get_logger
from app.models.agent_run import AgentStep
from app.models.recovery import RecoveryCase

log = get_logger(__name__)


async def _persist_steps(session: AsyncSession, case_id: str, decisions: list[dict[str, Any]]) -> None:
    """Mirror each node's decision into AgentStep rows for the trace UI."""
    for decision in decisions:
        session.add(
            AgentStep(
                case_id=case_id,
                thread_id=case_id,
                node=decision["node"],
                input=decision.get("input"),
                output=decision.get("output"),
                reasoning=decision.get("reasoning"),
                latency_ms=decision.get("latency_ms"),
            )
        )


async def run_case(case_id: str, session: AsyncSession) -> dict[str, Any]:
    """Run the recovery graph for one case to completion and persist the trace."""
    async with AsyncSqliteSaver.from_conn_string(settings.checkpoint_db) as checkpointer:
        graph = build_graph(session).compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": case_id}}
        result = await graph.ainvoke({"case_id": case_id, "thread_id": case_id}, config=config)

    await _persist_steps(session, case_id, result.get("decisions", []))
    await session.commit()
    return result


async def stream_case(case_id: str, session: AsyncSession) -> AsyncIterator[dict[str, Any]]:
    """Yield one event per node completion, for the SSE decision-trace endpoint."""
    async with AsyncSqliteSaver.from_conn_string(settings.checkpoint_db) as checkpointer:
        graph = build_graph(session).compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": case_id}}
        all_decisions: list[dict[str, Any]] = []

        async for event in graph.astream(
            {"case_id": case_id, "thread_id": case_id}, config=config, stream_mode="updates"
        ):
            for _node_name, node_output in event.items():
                decisions = node_output.get("decisions", []) if node_output else []
                all_decisions.extend(decisions)
                for decision in decisions:
                    yield decision

    await _persist_steps(session, case_id, all_decisions)
    await session.commit()


async def handle_outcome(case_id: str, recovered: bool, session: AsyncSession) -> str:
    """Apply a webhook-reported outcome (payment succeeded / retries exhausted)."""
    case = await session.get(RecoveryCase, case_id)
    if case is None:
        raise ValueError(f"RecoveryCase {case_id} not found")

    if not recovered:
        case.attempt_count += 1

    new_status = await evaluate_outcome(case, recovered, session)
    await session.commit()
    log.info("case outcome handled  case_id=%s  recovered=%s  status=%s", case_id, recovered, new_status)
    return new_status


async def find_case_by_payment_id(provider_payment_id: str, session: AsyncSession) -> RecoveryCase | None:
    return await session.scalar(
        select(RecoveryCase).where(RecoveryCase.provider_payment_id == provider_payment_id)
    )
