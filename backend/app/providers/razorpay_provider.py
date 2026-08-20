"""Razorpay payment provider adapter.

Wraps the official `razorpay` SDK behind the PaymentProvider interface.
Webhook signature verification follows Razorpay's documented scheme: HMAC-SHA256
of the *raw* request body against the configured webhook secret, compared with
`hmac.compare_digest` to avoid timing side channels.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import razorpay

from app.core.config import settings
from app.core.logging import get_logger
from app.providers.base import NormalizedFailure, PaymentProvider, RetryResult

log = get_logger(__name__)


class RazorpayProvider(PaymentProvider):
    name = "razorpay"

    def __init__(self) -> None:
        if not settings.razorpay_enabled:
            raise RuntimeError(
                "RazorpayProvider requires RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET"
            )
        self._client = razorpay.Client(
            auth=(settings.razorpay_key_id, settings.razorpay_key_secret)
        )

    async def retry_charge(self, provider_payment_id: str, amount_cents: int) -> RetryResult:
        """Re-capture a payment via Razorpay's Payments API.

        Razorpay does not offer a generic "retry" endpoint for card-based
        failures the way it does for e-mandates; the practical recovery path is
        capturing an authorized-but-uncaptured payment, or (for e-mandate /
        subscription flows) re-invoking the charge. This wraps `payment.capture`,
        which is the common case for the demo/mock parity path.
        """
        try:
            response = self._client.payment.capture(
                provider_payment_id, amount_cents, {"currency": "INR"}
            )
        except razorpay.errors.BadRequestError as exc:
            log.warning("razorpay retry_charge failed  payment_id=%s  error=%s",
                        provider_payment_id, exc)
            return RetryResult(
                succeeded=False,
                provider_payment_id=provider_payment_id,
                raw_response={"error": str(exc)},
                failure_code="RETRY_FAILED",
                failure_reason=str(exc),
            )

        return RetryResult(
            succeeded=response.get("status") == "captured",
            provider_payment_id=response.get("id", provider_payment_id),
            raw_response=response,
            failure_code=response.get("error_code"),
            failure_reason=response.get("error_description"),
        )

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        if not settings.razorpay_webhook_secret:
            log.warning("razorpay webhook secret not configured; rejecting webhook")
            return False
        expected = hmac.new(
            settings.razorpay_webhook_secret.encode(), raw_body, hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def parse_failure_event(self, payload: dict[str, Any]) -> NormalizedFailure:
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        return NormalizedFailure(
            provider_payment_id=entity.get("id"),
            failure_code=entity.get("error_code"),
            failure_reason=entity.get("error_description"),
            amount_cents=int(entity.get("amount", 0)),
            currency=entity.get("currency", "INR"),
        )
