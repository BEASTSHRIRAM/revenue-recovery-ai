"""Billing entities: customers, subscriptions, invoices.

These mirror what a payment provider already knows. The platform keeps a local
projection so recovery decisions can be made against history (has this customer
recovered before? how long have they been with us?) without a round trip per
decision.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.ids import new_id
from app.db.base import Base, StrEnumType, TimestampMixin
from app.models.enums import InvoiceStatus, SubscriptionStatus

if TYPE_CHECKING:
    from app.models.recovery import RecoveryCase


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("cus"))
    external_id: Mapped[str | None] = mapped_column(String(80), index=True)
    """The provider's own customer id, e.g. a Razorpay `cust_...`."""

    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), index=True)
    phone: Mapped[str | None] = mapped_column(String(32))
    locale: Mapped[str] = mapped_column(String(12), default="en-IN")
    country: Mapped[str] = mapped_column(String(2), default="IN")

    mrr_cents: Mapped[int] = mapped_column(Integer, default=0)
    """Monthly recurring revenue at stake if this customer churns."""

    tenure_days: Mapped[int] = mapped_column(Integer, default=0)
    """How long they have been a paying customer — a strong recoverability signal."""

    lifetime_recovered_cents: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_failed_count: Mapped[int] = mapped_column(Integer, default=0)
    lifetime_recovered_count: Mapped[int] = mapped_column(Integer, default=0)

    subscriptions: Mapped[list[Subscription]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )

    @property
    def historical_recovery_rate(self) -> float | None:
        """Share of this customer's past failures that were eventually recovered.

        None when they have no failure history — the agent must not treat
        "no data" as "never recovers".
        """
        if self.lifetime_failed_count == 0:
            return None
        return self.lifetime_recovered_count / self.lifetime_failed_count


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("sub"))
    external_id: Mapped[str | None] = mapped_column(String(80), index=True)
    customer_id: Mapped[str] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )

    plan_name: Mapped[str] = mapped_column(String(120))
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    interval: Mapped[str] = mapped_column(String(16), default="monthly")
    status: Mapped[SubscriptionStatus] = mapped_column(
        StrEnumType(SubscriptionStatus, 24), default=SubscriptionStatus.ACTIVE
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_billing_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped[Customer] = relationship(back_populates="subscriptions")
    invoices: Mapped[list[Invoice]] = relationship(
        back_populates="subscription", cascade="all, delete-orphan"
    )


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"
    __table_args__ = (Index("ix_invoices_status_due", "status", "due_at"),)

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("inv"))
    external_id: Mapped[str | None] = mapped_column(String(80), index=True)
    subscription_id: Mapped[str] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"), index=True
    )

    number: Mapped[str] = mapped_column(String(40))
    amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[InvoiceStatus] = mapped_column(StrEnumType(InvoiceStatus, 24), default=InvoiceStatus.DUE)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    subscription: Mapped[Subscription] = relationship(back_populates="invoices")
    cases: Mapped[list[RecoveryCase]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
