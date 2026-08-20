"""Payment provider registry — one factory, degrades safely."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.providers.base import NormalizedFailure, PaymentProvider, RetryResult
from app.providers.mock import MockPaymentProvider

__all__ = ["NormalizedFailure", "PaymentProvider", "RetryResult", "get_payment_provider"]


@lru_cache
def get_payment_provider() -> PaymentProvider:
    """Return the configured provider, falling back to mock without credentials.

    Uses `settings.effective_payment_provider`, which already encodes that
    fallback rule — this function just instantiates it.
    """
    if settings.effective_payment_provider == "razorpay":
        from app.providers.razorpay_provider import RazorpayProvider

        return RazorpayProvider()
    return MockPaymentProvider()
