"""Structured outputs the LLM is forced to produce via tool-calling.

Each of these is passed to `llm.with_structured_output(...)`, which makes Groq's
tool-calling machinery return exactly this shape instead of free text — no
manual JSON parsing, no "the model added a preamble" failure mode.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.enums import Channel, FailureClass


class TriageResult(BaseModel):
    """Output of the `triage` node: what a raw gateway decline actually means."""

    failure_class: FailureClass = Field(
        description="Normalised category for this decline, chosen from the fixed enum."
    )
    is_recoverable: bool = Field(
        description="Whether this specific failure is plausibly recoverable at all, "
        "independent of this customer's history."
    )
    rationale: str = Field(
        max_length=300,
        description="One sentence explaining why this gateway code maps to that class.",
    )


class ScoreResult(BaseModel):
    """Output of the `score` node: how likely this specific case is to recover."""

    recovery_score: float = Field(ge=0.0, le=1.0, description="Probability this case recovers.")
    confidence: float = Field(ge=0.0, le=1.0, description="Model's confidence in that estimate.")
    rationale: str = Field(max_length=300, description="One sentence citing the driving features.")


class MessageDraft(BaseModel):
    """One channel's drafted outreach copy."""

    channel: Channel
    subject: str | None = Field(default=None, max_length=150)
    body: str = Field(max_length=2000)


class ComposeResult(BaseModel):
    """Output of the `compose` node: one draft per channel in the strategy's ladder."""

    drafts: list[MessageDraft]
