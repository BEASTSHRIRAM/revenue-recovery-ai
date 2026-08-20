"""Payment provider abstraction.

Every payment gateway represents the same three operations differently: retry a
failed charge, verify a webhook signature, and normalise its own decline-code
vocabulary into something a human (or the agent) can reason about. Concrete
providers implement this interface; the rest of the app never imports Razorpay
or any other SDK directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RetryResult:
    """Outcome of attempting to re-charge a failed payment."""

    succeeded: bool
    provider_payment_id: str | None
    raw_response: dict[str, Any]
    failure_code: str | None = None
    failure_reason: str | None = None


@dataclass(frozen=True)
class NormalizedFailure:
    """A gateway's raw decline, before the agent's triage node classifies it further.

    This is deliberately *not* FailureClass — that classification is the agent's
    job. The provider only owns getting the raw code/description out of its own
    webhook or API payload shape.
    """

    provider_payment_id: str | None
    failure_code: str | None
    failure_reason: str | None
    amount_cents: int
    currency: str


class PaymentProvider(ABC):
    """Interface every payment gateway adapter (and the mock driver) implements."""

    name: str

    @abstractmethod
    async def retry_charge(self, provider_payment_id: str, amount_cents: int) -> RetryResult:
        """Attempt to re-present a failed charge for payment."""

    @abstractmethod
    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        """Verify a webhook payload actually came from this provider."""

    @abstractmethod
    def parse_failure_event(self, payload: dict[str, Any]) -> NormalizedFailure:
        """Extract the raw failure facts from a provider-shaped webhook payload."""
