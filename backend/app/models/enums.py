"""Domain enumerations.

`FailureClass` is the single most important type in this codebase: nearly every
recovery decision — whether to retry at all, when, over which channel, with what
tone — is a function of it. It is normalised from messy, vendor-specific gateway
codes by the agent's triage node.
"""

from __future__ import annotations

from enum import StrEnum


class FailureClass(StrEnum):
    """Why a charge failed, normalised across payment gateways."""

    INSUFFICIENT_FUNDS = "insufficient_funds"
    CARD_EXPIRED = "card_expired"
    CARD_INVALID = "card_invalid"
    DO_NOT_HONOR = "do_not_honor"
    AUTHENTICATION_REQUIRED = "authentication_required"
    RISK_BLOCKED = "risk_blocked"
    TECHNICAL_ERROR = "technical_error"
    HARD_DECLINE = "hard_decline"
    UNKNOWN = "unknown"

    @property
    def is_retryable(self) -> bool:
        """Whether re-presenting the same instrument can plausibly succeed.

        Retrying an expired or invalid card, a risk block, or a hard decline is
        pure waste — those need customer action or escalation, not another charge.
        """
        return self in {
            FailureClass.INSUFFICIENT_FUNDS,
            FailureClass.DO_NOT_HONOR,
            FailureClass.TECHNICAL_ERROR,
            FailureClass.UNKNOWN,
        }

    @property
    def needs_customer_action(self) -> bool:
        """Whether recovery requires the customer to do something (update card, authenticate)."""
        return self in {
            FailureClass.CARD_EXPIRED,
            FailureClass.CARD_INVALID,
            FailureClass.AUTHENTICATION_REQUIRED,
        }

    @property
    def is_terminal(self) -> bool:
        """Whether the issuer has said no in a way that will not change."""
        return self in {FailureClass.HARD_DECLINE, FailureClass.RISK_BLOCKED}


class CaseStatus(StrEnum):
    """Lifecycle of a recovery case."""

    OPEN = "open"                          # created, agent has not run yet
    IN_PROGRESS = "in_progress"            # strategy chosen, attempts scheduled
    AWAITING_CUSTOMER = "awaiting_customer"  # outreach sent, waiting on card update / auth
    RECOVERED = "recovered"                # payment collected
    LOST = "lost"                          # gave up: attempts exhausted or terminal decline
    ESCALATED = "escalated"                # handed to a human

    @property
    def is_closed(self) -> bool:
        return self in {CaseStatus.RECOVERED, CaseStatus.LOST}


class AttemptKind(StrEnum):
    RETRY_CHARGE = "retry_charge"
    OUTREACH = "outreach"


class AttemptOutcome(StrEnum):
    SCHEDULED = "scheduled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class Channel(StrEnum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class MessageStatus(StrEnum):
    DRAFT = "draft"            # generated, not cleared to send
    BLOCKED = "blocked"        # a guardrail rejected it; needs human eyes
    APPROVED = "approved"      # cleared, queued for the sender
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class InvoiceStatus(StrEnum):
    PAID = "paid"
    DUE = "due"
    PAST_DUE = "past_due"
    WRITTEN_OFF = "written_off"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    CANCELLED = "cancelled"
