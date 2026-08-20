"""API request/response schemas for recovery cases."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import CaseStatus, FailureClass


class CustomerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    mrr_cents: int
    tenure_days: int


class RecoveryAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    kind: str
    scheduled_at: datetime
    executed_at: datetime | None
    outcome: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    channel: str
    status: str
    subject: str | None
    body: str
    generated_by: str
    guardrail_flags: list[str] | None
    sent_at: datetime | None


class AgentStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    node: str
    reasoning: str | None
    output: dict[str, Any] | None
    latency_ms: int | None
    created_at: datetime


class CaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: CaseStatus
    failure_class: FailureClass
    recovery_score: float | None
    amount_at_risk_cents: int
    currency: str
    attempt_count: int
    opened_at: datetime
    closed_at: datetime | None


class CaseDetail(CaseListItem):
    failure_code: str | None
    failure_reason: str | None
    triage_rationale: str | None
    score_confidence: float | None
    strategy: dict[str, Any] | None
    attempts: list[RecoveryAttemptOut]
    messages: list[MessageOut]
    agent_steps: list[AgentStepOut]


class RunCaseResponse(BaseModel):
    case_id: str
    decisions: list[dict[str, Any]]
    status: CaseStatus


class OutcomeWebhookRequest(BaseModel):
    """Body accepted by the mock outcome webhook for demo/testing."""

    provider_payment_id: str
    recovered: bool
