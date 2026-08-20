"""Recovery case endpoints: list, detail, run the agent, approve a message."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.channels import get_channel_sender
from app.db.session import get_session
from app.models.billing import Customer, Invoice, Subscription
from app.models.enums import CaseStatus, FailureClass, MessageStatus
from app.models.message import Message
from app.models.recovery import RecoveryCase
from app.schemas.cases import CaseDetail, CaseListItem, RunCaseResponse
from app.services.recovery_service import run_case

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=list[CaseListItem])
async def list_cases(
    status: CaseStatus | None = None,
    failure_class: FailureClass | None = None,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
) -> list[RecoveryCase]:
    query = select(RecoveryCase).order_by(RecoveryCase.opened_at.desc())
    if status is not None:
        query = query.where(RecoveryCase.status == status)
    if failure_class is not None:
        query = query.where(RecoveryCase.failure_class == failure_class)
    query = query.offset(offset).limit(limit)
    return list((await session.scalars(query)).all())


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(case_id: str, session: AsyncSession = Depends(get_session)) -> RecoveryCase:
    case = await session.get(RecoveryCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    # Explicit refresh to eagerly populate the relationships CaseDetail needs —
    # lazy-loading them from a Pydantic serializer would require a greenlet
    # context we don't have at that point.
    await session.refresh(case, attribute_names=["attempts", "messages", "agent_steps"])
    return case


@router.post("/{case_id}/run", response_model=RunCaseResponse)
async def run_case_endpoint(
    case_id: str, session: AsyncSession = Depends(get_session)
) -> RunCaseResponse:
    case = await session.get(RecoveryCase, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")

    result = await run_case(case_id, session)
    await session.refresh(case)
    return RunCaseResponse(case_id=case_id, decisions=result.get("decisions", []), status=case.status)


@router.post("/{case_id}/messages/{message_id}/approve")
async def approve_message(
    case_id: str, message_id: str, session: AsyncSession = Depends(get_session)
) -> dict[str, str]:
    """Manually approve and send a message the guardrail blocked, or one held
    for human review under `require_human_approval`."""
    message = await session.get(Message, message_id)
    if message is None or message.case_id != case_id:
        raise HTTPException(status_code=404, detail="message not found")
    if message.status not in (MessageStatus.DRAFT, MessageStatus.BLOCKED):
        raise HTTPException(status_code=409, detail=f"message already {message.status.value}")

    case = await session.get(RecoveryCase, case_id)
    customer = await session.scalar(
        select(Customer)
        .join(Subscription, Subscription.customer_id == Customer.id)
        .join(Invoice, Invoice.subscription_id == Subscription.id)
        .where(Invoice.id == case.invoice_id)
    )
    to = customer.email if message.channel.value == "email" else customer.phone

    sender = get_channel_sender(message.channel.value)
    result = await sender.send(to or "", message.subject, message.body, case_id=case_id)

    message.status = MessageStatus.SENT if result.succeeded else MessageStatus.FAILED
    message.provider_message_id = result.provider_message_id
    await session.commit()
    return {"status": message.status.value}
