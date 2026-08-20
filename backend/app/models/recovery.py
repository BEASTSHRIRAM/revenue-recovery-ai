"""Recovery-side entities: the case, its attempts, and playbooks.

RecoveryCase is the central entity of the whole platform — one per failed
invoice, carrying the agent's classification, score, and lifecycle status.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.db.base import Base, TimestampMixin
from app.models.enums import AttemptKind, AttemptOutcome, CaseStatus, FailureClass

if TYPE_CHECKING:
    from app.models.agent_run import AgentStep
    from app.models.billing import Invoice
    from app.models.message import Message


class RecoveryCase(Base, TimestampMixin):
    __tablename__ = "recovery_cases"
    __table_args__ = (Index("ix_cases_status_class", "status", "failure_class"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("case"))
    invoice_id: Mapped[str] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), index=True
    )

    provider: Mapped[str] = mapped_column(String(24), default="mock")
    provider_payment_id: Mapped[str | None] = mapped_column(String(120), index=True)

    failure_code: Mapped[str | None] = mapped_column(String(80))
    """Raw decline code from the gateway, e.g. Razorpay's `BAD001`."""
    failure_reason: Mapped[str | None] = mapped_column(String(400))
    """Raw human-readable decline description from the gateway."""

    failure_class: Mapped[FailureClass] = mapped_column(
        String(32), default=FailureClass.UNKNOWN, index=True
    )
    """Normalised failure reason, assigned by the agent's triage node."""
    triage_rationale: Mapped[str | None] = mapped_column(String(500))

    recovery_score: Mapped[float | None] = mapped_column(Float)
    """0..1 probability estimate that this case is recoverable."""
    score_confidence: Mapped[float | None] = mapped_column(Float)

    status: Mapped[CaseStatus] = mapped_column(String(24), default=CaseStatus.OPEN, index=True)
    amount_at_risk_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)

    strategy: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    """Chosen retry ladder + channel plan, as emitted by the plan_retries node."""

    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    invoice: Mapped[Invoice] = relationship(back_populates="cases")
    attempts: Mapped[list[RecoveryAttempt]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="RecoveryAttempt.scheduled_at"
    )
    messages: Mapped[list[Message]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    agent_steps: Mapped[list[AgentStep]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="AgentStep.created_at"
    )


class RecoveryAttempt(Base, TimestampMixin):
    __tablename__ = "recovery_attempts"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("att"))
    case_id: Mapped[str] = mapped_column(
        ForeignKey("recovery_cases.id", ondelete="CASCADE"), index=True
    )

    kind: Mapped[AttemptKind] = mapped_column(String(20))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[AttemptOutcome] = mapped_column(String(20), default=AttemptOutcome.SCHEDULED)
    provider_response: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(String(400))

    case: Mapped[RecoveryCase] = relationship(back_populates="attempts")


class Playbook(Base, TimestampMixin):
    """Per-failure-class recovery policy, editable from the UI.

    Retry offsets are hours from case open. Win-rate counters update as cases
    close, so the numbers shown in the Playbooks page are live, not static config.
    """

    __tablename__ = "playbooks"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("pbk"))
    failure_class: Mapped[FailureClass] = mapped_column(String(32), unique=True, index=True)

    retry_offsets_hours: Mapped[list[int]] = mapped_column(JSON, default=list)
    channel_ladder: Mapped[list[str]] = mapped_column(JSON, default=list)
    """Ordered channels to escalate through, e.g. ["email", "sms", "whatsapp"]."""
    offer_policy: Mapped[str | None] = mapped_column(String(200))
    """Free-text policy hint fed to the compose node, e.g. "no discounts, single reminder"."""

    cases_closed: Mapped[int] = mapped_column(Integer, default=0)
    cases_recovered: Mapped[int] = mapped_column(Integer, default=0)

    @property
    def win_rate(self) -> float | None:
        if self.cases_closed == 0:
            return None
        return self.cases_recovered / self.cases_closed
