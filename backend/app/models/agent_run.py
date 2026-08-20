"""Persisted trace of every LangGraph node execution.

AgentStep is what makes the agent auditable: each node appends one row with its
inputs, outputs, and a plain-English reasoning summary, which is exactly what the
case-detail "decision trace" UI renders. Without this the agent is a black box.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.recovery import RecoveryCase


class AgentStep(Base, TimestampMixin):
    __tablename__ = "agent_steps"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("step"))
    case_id: Mapped[str] = mapped_column(
        ForeignKey("recovery_cases.id", ondelete="CASCADE"), index=True
    )
    thread_id: Mapped[str] = mapped_column(String(40), index=True)
    """LangGraph checkpoint thread id — equal to case_id so a case's run can be resumed."""

    node: Mapped[str] = mapped_column(String(40))
    input: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    reasoning: Mapped[str | None] = mapped_column(String(1000))
    """One-line plain-English summary of what this node decided and why."""

    latency_ms: Mapped[int | None] = mapped_column(Integer)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(String(1000))

    case: Mapped[RecoveryCase] = relationship(back_populates="agent_steps")
