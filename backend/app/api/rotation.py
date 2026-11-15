"""Rotation comparison: three strategies on one field (PDT 4.4, phase 6)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import SessionDep, require_roles
from app.core.parameters import get_config
from app.models import Field, Role, User
from app.schemas.rotation import RotationOut
from app.services.fields import visible_to
from app.services.water.rotation_service import parse_rotation, rotation_comparison
from app.services.water.vault import VaultError

router = APIRouter(prefix="/fields/{field_id}/rotation", tags=["rotation"])

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
        return rotation_comparison(session, field, parse_rotation(rotation), get_config())
    except VaultError as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": error.code, **error.details},
        ) from error
