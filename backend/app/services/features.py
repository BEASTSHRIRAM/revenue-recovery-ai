"""Deterministic feature engineering for the `enrich` node.

Everything here is plain arithmetic over facts already in the database. This is
intentional: the model should reason over facts, not guess at them. The `score`
node then blends its own judgment with `heuristic_prior` below, and is clamped
to stay close to it — one bad generation should not send a scoring decision far
from what the numbers already imply.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.billing import Customer
from app.models.enums import FailureClass
from app.models.recovery import RecoveryCase

# Indian salary cycles cluster around month-end/1st and, for a large working
# population, the 7th-10th (post-EMI-deduction). Insufficient-funds retries
# timed near a payday convert meaningfully better than a flat "retry in 1 hour".
_PAYDAY_DAYS_OF_MONTH = (1, 7, 30)


def days_to_next_payday(today: datetime | None = None) -> int:
    today = today or datetime.now(UTC)
    day = today.day
    upcoming = [d for d in _PAYDAY_DAYS_OF_MONTH if d >= day]
    if upcoming:
        return min(upcoming) - day
    # Wrap to the 1st of next month.
    return (31 - day) + 1


def build_features(
    customer: Customer, case: RecoveryCase, failure_class: FailureClass
) -> dict[str, float]:
    """Numeric signals the `score` node reasons over."""
    recovery_rate = customer.historical_recovery_rate
    return {
        "historical_recovery_rate": recovery_rate if recovery_rate is not None else 0.5,
        "has_recovery_history": 1.0 if recovery_rate is not None else 0.0,
        "tenure_days": float(customer.tenure_days),
        "tenure_score": min(customer.tenure_days / 365.0, 1.0),
        "mrr_at_risk_cents": float(customer.mrr_cents),
        "attempts_used": float(case.attempt_count),
        "attempts_remaining_ratio": max(0.0, 1.0 - case.attempt_count / 4.0),
        "days_to_next_payday": float(days_to_next_payday()),
        "failure_class_is_retryable": 1.0 if failure_class.is_retryable else 0.0,
        "failure_class_is_terminal": 1.0 if failure_class.is_terminal else 0.0,
    }


def heuristic_prior(features: dict[str, float]) -> float:
    """A cheap, fully-explainable recovery-probability estimate.

    Used as the anchor the LLM's own score gets clamped against, and as the
    score itself when Groq is not configured (stub mode).
    """
    if features["failure_class_is_terminal"]:
        return 0.05

    base = 0.35 if features["failure_class_is_retryable"] else 0.5
    base += 0.25 * features["historical_recovery_rate"]
    base += 0.1 * features["tenure_score"]
    base -= 0.08 * features["attempts_used"]
    return max(0.02, min(0.97, base))


def clamp_to_prior(model_score: float, prior: float, max_delta: float = 0.25) -> float:
    """Bound the LLM's score to prior ± max_delta so a bad generation can't
    swing the recovery strategy far from what the underlying numbers support.
    """
    lower, upper = prior - max_delta, prior + max_delta
    return max(0.0, min(1.0, max(lower, min(upper, model_score))))
