"""Playbook read/edit endpoints — the retry ladders and channel rules per
failure class, editable from the Playbooks page."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.recovery import Playbook
from app.schemas.playbooks import PlaybookOut, PlaybookUpdate

router = APIRouter(prefix="/api/playbooks", tags=["playbooks"])


@router.get("", response_model=list[PlaybookOut])
async def list_playbooks(session: AsyncSession = Depends(get_session)) -> list[Playbook]:
    return list((await session.scalars(select(Playbook))).all())


@router.put("/{playbook_id}", response_model=PlaybookOut)
async def update_playbook(
    playbook_id: str, payload: PlaybookUpdate, session: AsyncSession = Depends(get_session)
) -> Playbook:
    playbook = await session.get(Playbook, playbook_id)
    if playbook is None:
        raise HTTPException(status_code=404, detail="playbook not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(playbook, field, value)

    await session.commit()
    await session.refresh(playbook)
    return playbook
