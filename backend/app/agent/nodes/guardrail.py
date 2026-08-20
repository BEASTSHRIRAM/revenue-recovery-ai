"""`guardrail` — deterministic verification before anything is allowed to send.

This is the node that actually keeps the agent safe: no LLM call, just plain
checks against `state["facts"]` and hard limits from Settings. A draft that
fails any check is marked blocked and routed to human review instead of being
sent — the agent is never allowed to reason its way past this.
"""

from __future__ import annotations

import re
import time

from app.agent.state import RecoveryState
from app.core.config import settings

_REQUIRED_FOOTER_MARKERS = ("Billing Team", "billing", "support")


def _amount_matches(body: str, amount_cents: int, currency: str) -> bool:
    """The exact amount from facts must appear somewhere in the message.

    Rather than trying to parse every currency format a model might produce,
    check that *a* plausible rendering of the true amount is present, and that
    no *other* amount-like number in the body diverges from it by more than a
    rounding cent.
    """
    expected = amount_cents / 100
    expected_str = f"{expected:.2f}"
    expected_str_no_decimals = f"{expected:.0f}"
    return expected_str in body or expected_str_no_decimals in body


def _other_amounts_consistent(body: str, amount_cents: int) -> bool:
    """Flag bodies containing a second currency-like number that disagrees
    with the true amount — a common hallucination shape."""
    expected = amount_cents / 100
    numbers = re.findall(r"\d[\d,]*\.\d{2}", body)
    for raw in numbers:
        value = float(raw.replace(",", ""))
        if abs(value - expected) > 0.01:
            return False
    return True


def _check_draft(draft: dict, facts: dict) -> list[str]:
    flags: list[str] = []
    body = draft.get("body", "")

    if not _amount_matches(body, facts["amount_cents"], facts["currency"]):
        flags.append("amount_missing_or_mismatched")
    if not _other_amounts_consistent(body, facts["amount_cents"]):
        flags.append("conflicting_amount_present")

    if facts["case_id"] not in body and "/pay/" not in body:
        flags.append("missing_payment_link")

    if len(body) > 2000:
        flags.append("body_too_long")

    return flags


async def guardrail(state: RecoveryState) -> RecoveryState:
    started = time.monotonic()
    facts = state["facts"]
    drafts = state.get("drafts", [])

    all_flags: list[str] = []
    approved: list[dict] = []

    for draft in drafts:
        flags = _check_draft(draft, facts)
        if flags:
            all_flags.extend(f"{draft['channel']}:{flag}" for flag in flags)
        else:
            approved.append(draft)

    if settings.require_human_approval:
        all_flags.append("human_approval_required_by_policy")
        reasoning = f"{len(approved)} draft(s) passed checks but held for required human approval."
        approved = []
    elif all_flags:
        reasoning = f"{len(all_flags)} guardrail flag(s) raised: {all_flags}."
    else:
        reasoning = f"All {len(approved)} draft(s) passed guardrail checks; cleared to send."

    latency_ms = int((time.monotonic() - started) * 1000)
    return {
        "guardrail_flags": all_flags,
        "approved_drafts": approved,
        "decisions": [
            {
                "node": "guardrail",
                "reasoning": reasoning,
                "latency_ms": latency_ms,
                "output": {"flags": all_flags, "approved_count": len(approved)},
            }
        ],
    }
