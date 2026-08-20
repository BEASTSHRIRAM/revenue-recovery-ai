"""Simulated payment provider.

Drives the whole platform without any real credentials: retries succeed or fail
according to a deterministic-but-varied rule keyed off the payment id, and
webhook signatures are HMAC-SHA256 with a fixed dev secret so tests and the demo
flow can produce a valid signature locally.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from app.providers.base import NormalizedFailure, PaymentProvider, RetryResult

MOCK_WEBHOOK_SECRET = "mock-webhook-secret"


class MockPaymentProvider(PaymentProvider):
    name = "mock"

    async def retry_charge(self, provider_payment_id: str, amount_cents: int) -> RetryResult:
        # Deterministic pseudo-randomness so a given case behaves consistently
        # across repeated demo runs, without needing real state.
        digest = hashlib.sha256(provider_payment_id.encode()).hexdigest()
        succeeds = int(digest[:2], 16) % 5 != 0  # ~80% of retries succeed

        if succeeds:
            return RetryResult(
                succeeded=True,
                provider_payment_id=provider_payment_id,
                raw_response={"status": "captured", "amount": amount_cents},
            )
        return RetryResult(
            succeeded=False,
            provider_payment_id=provider_payment_id,
            raw_response={"status": "failed", "amount": amount_cents},
            failure_code="BAD001",
            failure_reason="The card was declined by the issuing bank.",
        )

    def verify_webhook_signature(self, raw_body: bytes, signature: str) -> bool:
        expected = hmac.new(MOCK_WEBHOOK_SECRET.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def parse_failure_event(self, payload: dict[str, Any]) -> NormalizedFailure:
        entity = payload.get("payload", {}).get("payment", {}).get("entity", payload)
        return NormalizedFailure(
            provider_payment_id=entity.get("id"),
            failure_code=entity.get("error_code"),
            failure_reason=entity.get("error_description"),
            amount_cents=int(entity.get("amount", 0)),
            currency=entity.get("currency", "INR"),
        )
