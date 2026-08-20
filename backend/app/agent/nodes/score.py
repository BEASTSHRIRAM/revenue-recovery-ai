"""`score` — estimate this specific case's recovery probability.

The LLM's score is clamped to `heuristic_prior(features) ± 0.25` (see
`app.services.features.clamp_to_prior`). This is a deliberate guardrail: the
model can nudge the estimate based on qualitative reading of the features, but
a single bad generation cannot send the recovery strategy somewhere the
underlying numbers don't support.
"""

from __future__ import annotations

import time

from app.agent.llm import get_llm
from app.agent.schemas import ScoreResult
from app.agent.state import RecoveryState
from app.agent.stub import stub_score
from app.core.config import settings
from app.core.logging import get_logger
from app.services.features import clamp_to_prior, heuristic_prior

log = get_logger(__name__)

_SYSTEM_PROMPT = """You estimate the probability that a failed subscription
payment will be successfully recovered, given engineered features about the
customer and case. Weigh historical recovery rate and tenure positively;
weigh attempts already used and terminal failure classes negatively. Return a
probability and your confidence in it, plus a one-sentence rationale citing
the specific features that drove your estimate."""


async def score(state: RecoveryState) -> RecoveryState:
    started = time.monotonic()
    features = state["features"]
    prior = heuristic_prior(features)

    if settings.groq_enabled:
        llm = get_llm().with_structured_output(ScoreResult)
        result: ScoreResult = await llm.ainvoke(
            [
                ("system", _SYSTEM_PROMPT),
                ("human", f"Features: {features}\nHeuristic prior estimate: {prior:.2f}"),
            ]
        )
        final_score = clamp_to_prior(result.recovery_score, prior)
        confidence = result.confidence
        rationale = result.rationale
    else:
        result = stub_score(prior)
        final_score = result.recovery_score
        confidence = result.confidence
        rationale = result.rationale

    latency_ms = int((time.monotonic() - started) * 1000)
    return {
        "recovery_score": final_score,
        "score_confidence": confidence,
        "decisions": [
            {
                "node": "score",
                "reasoning": f"{rationale} (prior={prior:.2f}, final={final_score:.2f})",
                "latency_ms": latency_ms,
                "output": {"recovery_score": final_score, "confidence": confidence},
            }
        ],
    }
