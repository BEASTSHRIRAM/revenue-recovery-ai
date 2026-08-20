"""The guardrail node is the platform's actual safety mechanism — it must
reliably catch a drafted message that states the wrong amount, and must never
let a flagged draft through as approved."""

from __future__ import annotations

import pytest

from app.agent.nodes.guardrail import guardrail

FACTS = {"case_id": "case_TEST01", "amount_cents": 299900, "currency": "INR"}


@pytest.mark.asyncio
async def test_correct_amount_passes():
    draft = {"channel": "email", "body": "Please pay 2999.00 INR at http://x/pay/case_TEST01"}
    result = await guardrail({"facts": FACTS, "drafts": [draft]})
    assert result["guardrail_flags"] == []
    assert result["approved_drafts"] == [draft]


@pytest.mark.asyncio
async def test_hallucinated_amount_is_blocked():
    draft = {"channel": "email", "body": "Please pay 5000.00 INR at http://x/pay/case_TEST01"}
    result = await guardrail({"facts": FACTS, "drafts": [draft]})
    assert any("amount" in flag for flag in result["guardrail_flags"])
    assert result["approved_drafts"] == []


@pytest.mark.asyncio
async def test_missing_amount_is_blocked():
    draft = {"channel": "sms", "body": "Please update your payment at http://x/pay/case_TEST01"}
    result = await guardrail({"facts": FACTS, "drafts": [draft]})
    assert "sms:amount_missing_or_mismatched" in result["guardrail_flags"]


@pytest.mark.asyncio
async def test_missing_payment_link_is_blocked():
    draft = {"channel": "email", "body": "Please pay 2999.00 INR to settle your account."}
    result = await guardrail({"facts": FACTS, "drafts": [draft]})
    assert "email:missing_payment_link" in result["guardrail_flags"]


@pytest.mark.asyncio
async def test_mixed_drafts_only_approve_the_clean_one():
    good = {"channel": "email", "body": "Please pay 2999.00 INR at http://x/pay/case_TEST01"}
    bad = {"channel": "sms", "body": "Please pay 1.00 INR at http://x/pay/case_TEST01"}
    result = await guardrail({"facts": FACTS, "drafts": [good, bad]})
    assert result["approved_drafts"] == [good]
    assert any(flag.startswith("sms:") for flag in result["guardrail_flags"])
