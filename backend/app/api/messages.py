"""WhatsApp message drafts: Zira writes, an agronomist approves, then it goes to the farmer."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.core.config import get_settings
from app.core.parameters import get_config
from app.models import Field, MessageDraft, Role, User
from app.schemas.messages import (
    ApproveIn,
    DraftOut,
    EditIn,
    GatewayOut,
    GenerateIn,
    GenerateOut,
)
from app.services.fields import visible_to
from app.services.messaging import drafts as service
from app.services.messaging.greenapi import GreenApiClient
from app.services.water.rotation_service import parse_rotation
from app.services.water.vault import VaultError

router = APIRouter(tags=["messages"])

Reviewer = Annotated[User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST))]


def get_gateway() -> GreenApiClient | None:
    """The WhatsApp gateway, or None when this server has no credentials (nothing is sent)."""
    settings = get_settings()
    return GreenApiClient.from_settings(settings) if settings.whatsapp_configured else None


GatewayDep = Annotated[GreenApiClient | None, Depends(get_gateway)]


def _out(draft: MessageDraft, field_name: str) -> DraftOut:
    phone = draft.recipient_phone
    return DraftOut(
        id=draft.id,
        field_id=draft.field_id,
        field_name=field_name,
        event_type=draft.event_type,
        event_date=draft.event_date,
        locale=draft.locale,
        body=draft.body,
        payload=draft.payload,
        status=draft.status,
        recipient_hint=f"…{phone[-4:]}" if phone else None,
        has_recipient=bool(phone),
        error=draft.error,
        created_at=draft.created_at,
        decided_at=draft.decided_at,
        sent_at=draft.sent_at,
    )


def _visible_draft(
    session: SessionDep, user: User, draft_id: uuid.UUID
) -> tuple[MessageDraft, Field]:
    row = session.execute(
        select(MessageDraft, Field)
        .join(Field, Field.id == MessageDraft.field_id)
        .where(MessageDraft.id == draft_id, visible_to(user))
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return row[0], row[1]


def _refuse(code: str, http_status: int = status.HTTP_422_UNPROCESSABLE_CONTENT, **details):
    return HTTPException(http_status, detail={"code": code, **details})


@router.get("/messages/gateway", response_model=GatewayOut)
def gateway_status(user: CurrentUser, gateway: GatewayDep) -> GatewayOut:
    return GatewayOut(configured=gateway is not None, provider="green_api")


@router.get("/messages", response_model=list[DraftOut])
def list_drafts(
    session: SessionDep,
    user: CurrentUser,
    draft_status: Annotated[str | None, Query(alias="status", max_length=16)] = None,
    field_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[DraftOut]:
    query = (
        select(MessageDraft, Field.name)
        .join(Field, Field.id == MessageDraft.field_id)
        .where(visible_to(user))
        .order_by(MessageDraft.event_date.desc(), MessageDraft.created_at.desc())
        .limit(limit)
    )
    if draft_status:
        query = query.where(MessageDraft.status == draft_status)
    if field_id:
        query = query.where(MessageDraft.field_id == field_id)
    return [_out(draft, name) for draft, name in session.execute(query)]


@router.post(
    "/fields/{field_id}/messages/generate",
    response_model=GenerateOut,
    status_code=status.HTTP_201_CREATED,
)
def generate(
    field_id: uuid.UUID, body: GenerateIn, session: SessionDep, user: Reviewer
) -> GenerateOut:
    field = session.scalar(select(Field).where(Field.id == field_id, visible_to(user)))
    if field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    try:
        created, skipped = service.generate_drafts(
            session,
            field,
            rotation=parse_rotation(body.rotation),
            season_year=body.season_year,
            locale=body.locale,
            recipient_phone=body.recipient_phone,
            config=get_config(),
        )
    except VaultError as error:
        raise _refuse(error.code, **error.details) from error
    except (service.DraftError, ValueError) as error:
        raise _refuse(getattr(error, "code", "invalid_phone")) from error
    session.commit()
    return GenerateOut(
        created=len(created), skipped=skipped, drafts=[_out(d, field.name) for d in created]
    )


@router.patch("/messages/{draft_id}", response_model=DraftOut)
def edit_draft(draft_id: uuid.UUID, body: EditIn, session: SessionDep, user: Reviewer) -> DraftOut:
    draft, field = _visible_draft(session, user, draft_id)
    try:
        service.edit(draft, body=body.body, recipient_phone=body.recipient_phone)
    except (service.DraftError, ValueError) as error:
        raise _refuse(getattr(error, "code", "invalid_phone")) from error
    session.commit()
    return _out(draft, field.name)


@router.post("/messages/{draft_id}/approve", response_model=DraftOut)
def approve_draft(
    draft_id: uuid.UUID, body: ApproveIn, session: SessionDep, user: Reviewer, gateway: GatewayDep
) -> DraftOut:
    draft, field = _visible_draft(session, user, draft_id)
    try:
        if body.recipient_phone:
            service.edit(draft, body=None, recipient_phone=body.recipient_phone)
        service.approve(draft, user, gateway=gateway)
    except (service.DraftError, ValueError) as error:
        raise _refuse(getattr(error, "code", "invalid_phone")) from error
    session.commit()
    return _out(draft, field.name)


@router.post("/messages/{draft_id}/send", response_model=DraftOut)
def send_draft(
    draft_id: uuid.UUID, session: SessionDep, user: Reviewer, gateway: GatewayDep
) -> DraftOut:
    """Try again for a draft that is approved but was not sent (no gateway, or it failed)."""
    draft, field = _visible_draft(session, user, draft_id)
    try:
        service.send(draft, gateway=gateway)
    except service.DraftError as error:
        raise _refuse(error.code) from error
    session.commit()
    return _out(draft, field.name)


@router.post("/messages/{draft_id}/reject", response_model=DraftOut)
def reject_draft(draft_id: uuid.UUID, session: SessionDep, user: Reviewer) -> DraftOut:
    draft, field = _visible_draft(session, user, draft_id)
    try:
        service.reject(draft, user)
    except service.DraftError as error:
        raise _refuse(error.code) from error
    session.commit()
    return _out(draft, field.name)
