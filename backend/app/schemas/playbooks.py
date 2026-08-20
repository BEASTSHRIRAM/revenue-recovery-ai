"""API schemas for playbook read/edit."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.models.enums import FailureClass


class PlaybookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    failure_class: FailureClass
    retry_offsets_hours: list[int]
    channel_ladder: list[str]
    offer_policy: str | None
    cases_closed: int
    cases_recovered: int
    win_rate: float | None


class PlaybookUpdate(BaseModel):
    retry_offsets_hours: list[int] | None = None
    channel_ladder: list[str] | None = None
    offer_policy: str | None = None
