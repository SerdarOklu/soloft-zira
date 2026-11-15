"""Cooperative panel and farmer view (phase 7, PDT 10.3).

A cooperative user creates farmer accounts for their own organization and links fields to
them; an admin can do the same anywhere. A farmer sees only their own fields and the messages
that were sent to them, never a draft.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import SessionDep, require_roles
from app.cli import create_user
from app.core.parameters import get_config
from app.models import (
    Field,
    MessageDraft,
    Organization,
    Role,
    User,
    WeatherObservation,
)
from app.schemas.users import (
    FarmerField,
    FarmerMessage,
    FarmerSummary,
    FarmerWater,
    LinkFarmer,
    UserCreate,
    UserOut,
    UserPatch,
)
from app.services.fields import visible_to
from app.services.messaging.drafts import SENT
from app.services.power import SOURCE as POWER_SOURCE
from app.services.water.vault import VaultError, water_vault

router = APIRouter(tags=["cooperative"])

Manager = Annotated[User, Depends(require_roles(Role.ADMIN, Role.COOPERATIVE_USER))]
Farmer = Annotated[User, Depends(require_roles(Role.FARMER))]

DEFAULT_CROP = "winter_wheat"
MESSAGE_LIMIT = 20


def _refuse(code: str, http_status: int = status.HTTP_422_UNPROCESSABLE_CONTENT):
    return HTTPException(http_status, detail={"code": code})


def _out(session: SessionDep, user: User) -> UserOut:
    count = session.scalar(
        select(func.count()).select_from(Field).where(Field.farmer_user_id == user.id)
    )
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        organization_id=user.organization_id,
        is_active=user.is_active,
        field_count=count or 0,
        created_at=user.created_at,
    )


def _manageable(session: SessionDep, manager: User, user_id: uuid.UUID) -> User:
    """A user this manager may change: any for an admin, the farmers of their own organization
    for a cooperative user."""
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    if manager.role != Role.ADMIN and (
        user.role != Role.FARMER
        or manager.organization_id is None
        or user.organization_id != manager.organization_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(session: SessionDep, manager: Manager) -> list[UserOut]:
    query = select(User).order_by(User.name)
    if manager.role != Role.ADMIN:
        if manager.organization_id is None:
            return []
        query = query.where(
            User.organization_id == manager.organization_id, User.role == Role.FARMER
        )
    return [_out(session, user) for user in session.scalars(query)]


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def add_user(body: UserCreate, session: SessionDep, manager: Manager) -> UserOut:
    if manager.role == Role.ADMIN:
        role, organization_id = Role(body.role), body.organization_id
        if organization_id is not None and session.get(Organization, organization_id) is None:
            raise _refuse("unknown_organization")
    else:
        # A cooperative user creates farmers, in their own organization only.
        if body.role != "farmer":
            raise _refuse("only_farmers", status.HTTP_403_FORBIDDEN)
        if manager.organization_id is None:
            raise _refuse("no_organization")
        role, organization_id = Role.FARMER, manager.organization_id
    try:
        user = create_user(
            session, email=body.email, name=body.name, role=role, password=body.password
        )
    except ValueError as error:
        raise _refuse(
            "email_taken" if "already exists" in str(error) else "invalid_user"
        ) from error
    user.organization_id = organization_id
    session.commit()
    return _out(session, user)


@router.patch("/users/{user_id}", response_model=UserOut)
def change_user(
    user_id: uuid.UUID, body: UserPatch, session: SessionDep, manager: Manager
) -> UserOut:
    user = _manageable(session, manager, user_id)
    if user.id == manager.id and body.is_active is False:
        raise _refuse("cannot_deactivate_yourself")
    if body.name is not None:
        user.name = body.name.strip()
    if body.is_active is not None:
        user.is_active = body.is_active
    session.commit()
    return _out(session, user)


@router.patch("/fields/{field_id}/farmer", response_model=LinkFarmer)
def link_farmer(
    field_id: uuid.UUID, body: LinkFarmer, session: SessionDep, user: Manager
) -> LinkFarmer:
    """Link a field to a farmer, or unlink it with null."""
    field = session.scalar(select(Field).where(Field.id == field_id, visible_to(user)))
    if field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    if body.farmer_user_id is not None:
        farmer = _manageable(session, user, body.farmer_user_id)
        if farmer.role != Role.FARMER:
            raise _refuse("not_a_farmer")
    field.farmer_user_id = body.farmer_user_id
    session.commit()
    return LinkFarmer(farmer_user_id=field.farmer_user_id)


@router.get("/farmer/summary", response_model=FarmerSummary)
def farmer_summary(session: SessionDep, user: Farmer) -> FarmerSummary:
    """What a farmer sees: their fields with the water on the latest decision day, and the
    messages that were sent to them."""
    config = get_config()
    fields = list(
        session.scalars(select(Field).where(Field.farmer_user_id == user.id).order_by(Field.name))
    )
    cards = []
    for field in fields:
        water, problem = None, None
        mode: str = "satellite"
        try:
            vault = water_vault(session, field, DEFAULT_CROP, None, config)
            decision = vault.decision
            water = FarmerWater(
                date=vault.date,
                storage_mm=decision.storage_mm,
                low_mm=decision.low_mm,
                high_mm=decision.high_mm,
                taw_mm=decision.taw_mm,
                fill_fraction=decision.fill_fraction,
            )
            mode = vault.mode
        except VaultError as error:
            problem = error.code
        last_day = session.scalar(
            select(func.max(WeatherObservation.date)).where(
                WeatherObservation.field_id == field.id,
                WeatherObservation.source == POWER_SOURCE,
            )
        )
        cards.append(
            FarmerField(
                id=field.id,
                name=field.name,
                region=field.region,
                area_ha=field.area_ha,
                mode=mode,  # type: ignore[arg-type]
                water=water,
                water_problem=problem,
                last_weather_date=last_day,
            )
        )
    rows = session.execute(
        select(MessageDraft, Field.name)
        .join(Field, Field.id == MessageDraft.field_id)
        .where(Field.farmer_user_id == user.id, MessageDraft.status == SENT)
        .order_by(MessageDraft.sent_at.desc().nullslast(), MessageDraft.event_date.desc())
        .limit(MESSAGE_LIMIT)
    )
    return FarmerSummary(
        name=user.name,
        fields=cards,
        messages=[
            FarmerMessage(
                id=draft.id,
                field_name=name,
                event_type=draft.event_type,
                event_date=draft.event_date,
                body=draft.body,
                sent_at=draft.sent_at,
            )
            for draft, name in rows
        ],
    )
