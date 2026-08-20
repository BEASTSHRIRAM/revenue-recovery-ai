"""`triage` — classify why the charge actually failed.

Gateway decline codes are messy and vendor-specific ("BAD001", "GEN001" and
worse in production). Mapping them to a fixed FailureClass is exactly the kind
of fuzzy-input-to-fixed-taxonomy task an LLM is good at, so this node calls
Groq with structured output when available and falls back to a small lookup
table (`stub_triage`) otherwise.
"""

from __future__ import annotations

import time

from app.agent.llm import get_llm
from app.agent.schemas import TriageResult
from app.agent.state import RecoveryState
from app.agent.stub import stub_triage
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

_SYSTEM_PROMPT = """You classify why a subscription payment charge failed.

You are given a raw gateway decline code and description. Map it to exactly
one FailureClass. Be conservative: if the code is ambiguous or unfamiliar,
prefer `unknown` over guessing a specific class. Do not invent facts about
the customer or transaction beyond what's given."""


async def triage(state: RecoveryState) -> RecoveryState:
    started = time.monotonic()
    facts = state["facts"]
    failure_code = facts.get("failure_code")
    failure_reason = facts.get("failure_reason")

    if settings.groq_enabled:
        llm = get_llm().with_structured_output(TriageResult)
        result: TriageResult = await llm.ainvoke(
            [
                ("system", _SYSTEM_PROMPT),
                (
                    "human",
                    f"Gateway code: {failure_code}\nGateway description: {failure_reason}",
                ),
            ]
        )
    else:
        result = stub_triage(failure_code, failure_reason)

    latency_ms = int((time.monotonic() - started) * 1000)
    return {
        "failure_class": result.failure_class,
        "is_recoverable": result.is_recoverable,
        "triage_rationale": result.rationale,
        "decisions": [
            {
                "node": "triage",
                "reasoning": result.rationale,
                "latency_ms": latency_ms,
                "output": {
                    "failure_class": result.failure_class.value,
                    "is_recoverable": result.is_recoverable,
                },
            }
        ],
    }
