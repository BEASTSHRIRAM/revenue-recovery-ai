"""Declarative base and shared column mixins."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


def utcnow() -> datetime:
    """Timezone-aware now. Used as a Python-side default so tests can freeze it."""
    return datetime.now(UTC)


class StrEnumType(TypeDecorator):
    """Stores a StrEnum member as its plain string value, and coerces it back
    to the enum on read.

    Plain `mapped_column(String(32))` with a StrEnum Python type looks correct
    at write time (StrEnum *is* a str) but silently hands back a bare `str` on
    every read — any downstream code calling `.is_retryable` or `.value` on a
    freshly-loaded row then breaks. This closes that gap without touching the
    underlying VARCHAR column, so no migration change is needed.
    """

    impl = String
    cache_ok = True

    def __init__(self, enum_cls: type[StrEnum], length: int = 32) -> None:
        super().__init__(length=length)
        self._enum_cls = enum_cls

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return self._enum_cls(value).value

    def process_result_value(self, value: Any, dialect: Any) -> StrEnum | None:
        if value is None:
            return None
        return self._enum_cls(value)


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
