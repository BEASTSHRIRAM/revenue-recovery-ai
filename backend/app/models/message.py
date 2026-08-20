"""Customer-facing messages drafted and (optionally) sent by the agent."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.db.base import Base, TimestampMixin
from app.models.enums import Channel, MessageStatus

if TYPE_CHECKING:
    from app.models.recovery import RecoveryCase


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("msg"))
    case_id: Mapped[str] = mapped_column(
        ForeignKey("recovery_cases.id", ondelete="CASCADE"), index=True
    )

    channel: Mapped[Channel] = mapped_column(String(16))
    status: Mapped[MessageStatus] = mapped_column(String(16), default=MessageStatus.DRAFT)

    subject: Mapped[str | None] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(String(4000))

    generated_by: Mapped[str] = mapped_column(String(40), default="stub")
    """Model id that produced this draft, e.g. "grok-4.6" or "stub"."""
    guardrail_flags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    provider_message_id: Mapped[str | None] = mapped_column(String(120))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    case: Mapped[RecoveryCase] = relationship(back_populates="messages")
