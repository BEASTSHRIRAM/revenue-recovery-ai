"""LangGraph state for a single recovery case run.

One `RecoveryState` flows through the whole graph for a given case (thread_id =
case_id), accumulating facts as each node runs. Kept as a TypedDict, which is
what LangGraph's StateGraph expects and merges via reducers.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from app.models.enums import FailureClass


def _append(old: list[Any] | None, new: list[Any]) -> list[Any]:
    """Reducer for fields every node appends to instead of overwriting."""
    return (old or []) + new


class RecoveryState(TypedDict, total=False):
    # ---------- identity ----------
    case_id: str
    thread_id: str

    # ---------- facts (loaded by `ingest`, read-only after) ----------
    facts: dict[str, Any]
    """Ground truth for this case: invoice amount/currency, customer, prior
    engagement. Every number the compose node writes into a message must trace
    back to this dict — that is what the guardrail node checks."""

    # ---------- triage ----------
    failure_class: FailureClass
    is_recoverable: bool
    triage_rationale: str

    # ---------- enrichment (deterministic) ----------
    features: dict[str, float]
    """Numeric signals the score node reasons over: historical_recovery_rate,
    attempts_used, tenure_days, mrr_at_risk_cents, days_to_next_payday, etc."""

    # ---------- scoring ----------
    recovery_score: float
    score_confidence: float

    # ---------- strategy ----------
    strategy: dict[str, Any]
    """Chosen retry ladder + channel plan, as produced by plan_retries."""

    # ---------- drafts ----------
    drafts: Annotated[list[dict[str, Any]], _append]
    """One entry per channel: {channel, subject, body}."""

    # ---------- guardrail ----------
    guardrail_flags: Annotated[list[str], _append]
    approved_drafts: list[dict[str, Any]]

    # ---------- control flow ----------
    next_action: str
    """Which branch `route` sends this case down: plan_retries | compose | escalate."""

    # ---------- audit trail ----------
    decisions: Annotated[list[dict[str, Any]], _append]
    """Every node appends {node, reasoning, latency_ms} here; mirrored to the
    AgentStep table for the case-detail decision-trace UI."""
