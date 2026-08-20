"""`route` — plain conditional edge, no LLM.

Deliberately cheap and fully deterministic: which branch a case takes should
be debuggable by reading an if-statement, not by re-running a model call. The
LLM's job was upstream (triage, score); this just acts on its output.
"""

from __future__ import annotations

from typing import Literal

from app.agent.state import RecoveryState

RouteDecision = Literal["plan_retries", "compose_action_required", "escalate"]


def route(state: RecoveryState) -> RouteDecision:
    failure_class = state["failure_class"]
    recovery_score = state.get("recovery_score", 0.0)

    if failure_class.is_terminal:
        return "escalate"

    if failure_class.needs_customer_action:
        # Card expired / invalid / auth required: retrying the same instrument
        # is wasted effort. The only useful action is asking the customer to
        # act, so skip straight to composing outreach.
        return "compose_action_required"

    if recovery_score < 0.1:
        return "escalate"

    return "plan_retries"
