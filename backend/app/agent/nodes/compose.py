"""`compose` — write the customer-facing message copy.

Drafts one message per channel in the strategy's ladder, tuned to tenure and
amount. Every number/date the copy states must come from `state["facts"]` —
the prompt is instructed accordingly, and the `guardrail` node downstream
verifies it rather than trusting the instruction alone.
"""

from __future__ import annotations

import time

from app.agent.llm import get_llm
from app.agent.schemas import ComposeResult
from app.agent.state import RecoveryState
from app.agent.stub import stub_compose
from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)

_SYSTEM_PROMPT = """You write short, plain-language billing recovery messages
for a subscription business. Write one draft per requested channel.

Rules:
- State the exact amount and currency given in the facts. Never invent or
  round a different number.
- Never mention any customer, amount, or detail not present in the facts.
- Tone: calm and helpful, never guilt-tripping or urgent-sounding. A customer
  whose card expired is not at fault.
- Exactly one clear call to action: the payment update link provided.
- Email drafts get a subject line under 80 characters; SMS/WhatsApp drafts
  have no subject and must fit in roughly 300 characters.
- Do not offer discounts or promises the policy hint doesn't authorize."""


async def compose(state: RecoveryState) -> RecoveryState:
    started = time.monotonic()
    facts = state["facts"]
    strategy = state["strategy"]
    failure_class = state["failure_class"]
    channels = strategy["channel_ladder"]

    amount_display = f"{facts['amount_cents'] / 100:.2f} {facts['currency']}"
    update_url = f"{settings.public_app_url}/pay/{facts['case_id']}"

    if settings.groq_enabled:
        llm = get_llm().with_structured_output(ComposeResult)
        human_prompt = (
            f"Customer: {facts['customer_name']}\n"
            f"Amount due: {amount_display}\n"
            f"Invoice: {facts['invoice_number']}\n"
            f"Failure reason (customer-safe framing needed): {failure_class.value}\n"
            f"Payment update link: {update_url}\n"
            f"Channels to draft: {channels}\n"
            f"Offer policy: {strategy.get('offer_policy') or 'none'}"
        )
        result: ComposeResult = await llm.ainvoke(
            [("system", _SYSTEM_PROMPT), ("human", human_prompt)]
        )
    else:
        result = stub_compose(
            failure_class, channels, facts["customer_name"], amount_display, update_url
        )

    drafts = [d.model_dump(mode="json") for d in result.drafts]
    latency_ms = int((time.monotonic() - started) * 1000)
    return {
        "drafts": drafts,
        "decisions": [
            {
                "node": "compose",
                "reasoning": f"Drafted {len(drafts)} message(s) over {channels}.",
                "latency_ms": latency_ms,
                "output": {"channels": channels},
            }
        ],
    }
