"""Rotation comparison: three strategies on one field (PDT 4.4, phase 6)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import SessionDep, require_roles
from app.core.parameters import get_config
from app.models import CropCycle, CycleSource, Field, Role, User
from app.schemas.rotation import RotationOut
from app.services import field_memory
from app.services.fields import visible_to
from app.services.water.rotation_service import parse_rotation, rotation_comparison
from app.services.water.vault import VaultError

router = APIRouter(prefix="/fields/{field_id}/rotation", tags=["rotation"])

HISTORY = "history"  # strategy A from the history a person confirmed in Field Memory
MIN_CONFIRMED_SEASONS = 2


def confirmed_rotation(session: SessionDep, field: Field) -> list[str | None]:
    """The confirmed seasons of the field, oldest first, as a rotation (PDT 4.1, 7.8)."""
    cycles = session.scalars(
        select(CropCycle)
        .where(
            CropCycle.field_id == field.id,
            CropCycle.confirmed_at.is_not(None),
            CropCycle.source.in_([CycleSource.USER, CycleSource.AGRONOMIST]),
        )
        .order_by(CropCycle.season)
    ).all()
    states = [cycle.state.value for cycle in cycles if cycle.state.value != field_memory.UNKNOWN]
    if len(states) < MIN_CONFIRMED_SEASONS:
        raise VaultError("history_not_confirmed")
    return field_memory.rotation_from_history(states)


StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]


@router.get("", response_model=RotationOut)
def read_rotation(
    field_id: uuid.UUID,
    session: SessionDep,
    user: StaffUser,
    rotation: Annotated[str | None, Query(max_length=200)] = None,
) -> RotationOut:
    """Strategies A, B and C over the stored weather record.

    ``rotation`` is the current rotation, comma separated (``winter_wheat,fallow``); it is
    user-supplied until Field Memory exists.
    """
    field = session.scalar(select(Field).where(Field.id == field_id, visible_to(user)))
    if field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    try:
        if rotation == HISTORY:
            sequence = confirmed_rotation(session, field)
        else:
            sequence = parse_rotation(rotation)
        return rotation_comparison(session, field, sequence, get_config())
    except VaultError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": error.code, **error.details},
        ) from error
