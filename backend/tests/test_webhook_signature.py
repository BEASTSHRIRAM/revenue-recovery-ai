"""Webhook signature verification must reject anything not signed with the
correct secret, over both providers' schemes."""

from __future__ import annotations

import hashlib
import hmac

from app.providers.mock import MOCK_WEBHOOK_SECRET, MockPaymentProvider
from app.providers.razorpay_provider import RazorpayProvider


def test_mock_provider_accepts_correctly_signed_body():
    provider = MockPaymentProvider()
    body = b'{"event": "payment.failed"}'
    signature = hmac.new(MOCK_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    assert provider.verify_webhook_signature(body, signature) is True


def test_mock_provider_rejects_wrong_signature():
    provider = MockPaymentProvider()
    body = b'{"event": "payment.failed"}'
    assert provider.verify_webhook_signature(body, "not-the-right-signature") is False


def test_mock_provider_rejects_tampered_body():
    provider = MockPaymentProvider()
    body = b'{"event": "payment.failed"}'
    signature = hmac.new(MOCK_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    tampered = b'{"event": "payment.captured"}'
    assert provider.verify_webhook_signature(tampered, signature) is False


def test_razorpay_provider_verifies_against_configured_secret(monkeypatch):
    monkeypatch.setattr("app.providers.razorpay_provider.settings.razorpay_webhook_secret", "topsecret")
    monkeypatch.setattr("app.providers.razorpay_provider.settings.razorpay_key_id", "rzp_test_id")
    monkeypatch.setattr("app.providers.razorpay_provider.settings.razorpay_key_secret", "rzp_test_secret")

    provider = RazorpayProvider()
    body = b'{"event": "payment.failed"}'
    signature = hmac.new(b"topsecret", body, hashlib.sha256).hexdigest()
    assert provider.verify_webhook_signature(body, signature) is True
    assert provider.verify_webhook_signature(body, "wrong") is False


def test_razorpay_provider_rejects_when_secret_missing(monkeypatch):
    monkeypatch.setattr("app.providers.razorpay_provider.settings.razorpay_webhook_secret", None)
    monkeypatch.setattr("app.providers.razorpay_provider.settings.razorpay_key_id", "rzp_test_id")
    monkeypatch.setattr("app.providers.razorpay_provider.settings.razorpay_key_secret", "rzp_test_secret")

    provider = RazorpayProvider()
    assert provider.verify_webhook_signature(b"{}", "anything") is False
