"""Declarative base and shared column mixins."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Timezone-aware now. Used as a Python-side default so tests can freeze it."""
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Shared declarative base for every ORM model."""


class TimestampMixin:
    """created_at / updated_at maintained by the database where possible."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
