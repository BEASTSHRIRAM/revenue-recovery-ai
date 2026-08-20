"""Deterministic fallback reasoning used when GROQ_API_KEY is not set.

The platform must work end to end with zero credentials, so every LLM-backed
node has a rule-based twin here. These are deliberately simple — good enough to
drive a believable demo and to keep the graph's control flow exercised in
tests — not an attempt to approximate what Groq would actually decide.
"""

from __future__ import annotations

from app.agent.schemas import ComposeResult, MessageDraft, ScoreResult, TriageResult
from app.models.enums import Channel, FailureClass

# Gateway codes are vendor-specific noise; this is a small illustrative mapping
# covering the codes the seed data and mock provider actually produce. A real
# Groq-backed triage node handles codes outside this table by design.
_CODE_TO_CLASS: dict[str, FailureClass] = {
    "BAD001": FailureClass.INSUFFICIENT_FUNDS,
    "BAD002": FailureClass.CARD_EXPIRED,
    "BAD003": FailureClass.CARD_INVALID,
    "BAD005": FailureClass.AUTHENTICATION_REQUIRED,
    "BAD009": FailureClass.HARD_DECLINE,
    "GEN001": FailureClass.DO_NOT_HONOR,
    "GTW001": FailureClass.TECHNICAL_ERROR,
    "SEC001": FailureClass.RISK_BLOCKED,
}


def stub_triage(failure_code: str | None, failure_reason: str | None) -> TriageResult:
    failure_class = _CODE_TO_CLASS.get((failure_code or "").upper(), FailureClass.UNKNOWN)
    return TriageResult(
        failure_class=failure_class,
        is_recoverable=failure_class.is_retryable or failure_class.needs_customer_action,
        rationale=f"Stub mapping of gateway code {failure_code!r} to {failure_class.value}.",
    )


def stub_score(prior: float) -> ScoreResult:
    return ScoreResult(
        recovery_score=round(prior, 3),
        confidence=0.5,
        rationale="Stub mode: score is the deterministic heuristic prior, unadjusted by an LLM.",
    )


_SUBJECT_BY_CLASS: dict[FailureClass, str] = {
    FailureClass.INSUFFICIENT_FUNDS: "Your payment didn't go through — we'll try again",
    FailureClass.CARD_EXPIRED: "Please update your expired card",
    FailureClass.CARD_INVALID: "We couldn't process your card — please double-check it",
    FailureClass.DO_NOT_HONOR: "Your recent payment was declined",
    FailureClass.AUTHENTICATION_REQUIRED: "Action needed: verify your payment",
    FailureClass.RISK_BLOCKED: "We need to verify your recent payment",
    FailureClass.TECHNICAL_ERROR: "We're retrying your payment",
    FailureClass.HARD_DECLINE: "We couldn't process your payment",
    FailureClass.UNKNOWN: "There was an issue with your recent payment",
}


def stub_compose(
    failure_class: FailureClass,
    channels: list[str],
    customer_name: str,
    amount_display: str,
    update_payment_url: str,
) -> ComposeResult:
    """Template-based drafts. Deliberately plain — this is the fallback path,
    not the product's actual voice, which comes from Groq in compose.py.
    """
    subject = _SUBJECT_BY_CLASS[failure_class]
    body = (
        f"Hi {customer_name},\n\n"
        f"We tried to process your payment of {amount_display} and it didn't go through.\n\n"
        f"You can update your payment details or retry here: {update_payment_url}\n\n"
        f"Thanks,\nBilling Team"
    )
    drafts = [
        MessageDraft(channel=Channel(channel), subject=subject if channel == "email" else None, body=body)
        for channel in channels
    ]
    return ComposeResult(drafts=drafts)
