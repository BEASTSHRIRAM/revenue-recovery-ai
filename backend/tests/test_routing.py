"""route() is a plain conditional edge — verify every branch by name rather
than by re-running the whole graph, since that's the point of keeping it
deterministic."""

from __future__ import annotations

from app.agent.nodes.route import route
from app.models.enums import FailureClass


def test_terminal_failure_escalates():
    assert route({"failure_class": FailureClass.HARD_DECLINE, "recovery_score": 0.9}) == "escalate"
    assert route({"failure_class": FailureClass.RISK_BLOCKED, "recovery_score": 0.9}) == "escalate"


def test_needs_customer_action_skips_retry():
    for failure_class in (
        FailureClass.CARD_EXPIRED,
        FailureClass.CARD_INVALID,
        FailureClass.AUTHENTICATION_REQUIRED,
    ):
        result = route({"failure_class": failure_class, "recovery_score": 0.9})
        assert result == "compose_action_required"


def test_very_low_score_escalates_even_if_retryable():
    result = route({"failure_class": FailureClass.INSUFFICIENT_FUNDS, "recovery_score": 0.05})
    assert result == "escalate"


def test_normal_retryable_case_plans_retries():
    result = route({"failure_class": FailureClass.INSUFFICIENT_FUNDS, "recovery_score": 0.6})
    assert result == "plan_retries"


def test_missing_score_defaults_to_zero_and_escalates():
    result = route({"failure_class": FailureClass.TECHNICAL_ERROR})
    assert result == "escalate"
