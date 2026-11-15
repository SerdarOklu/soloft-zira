"""Water Vault: the usable water on a decision day (PDT section 4.3, phase 4)."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import SessionDep, require_roles
from app.core.parameters import get_config
from app.models import Field, Role, User
from app.schemas.water import WaterVaultOut
from app.services.fields import visible_to
from app.services.water.vault import VaultError, water_vault

router = APIRouter(prefix="/fields/{field_id}/water-vault", tags=["water-vault"])

StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]


@router.get("", response_model=WaterVaultOut)
def read_water_vault(
    field_id: uuid.UUID,
    session: SessionDep,
    user: StaffUser,
    crop: Annotated[str, Query(min_length=1, max_length=64)],
    on: Annotated[date | None, Query(alias="date")] = None,
) -> WaterVaultOut:
    """The water in the root zone on ``date`` for the chosen crop, with its range.

    Without a date the most recent decision day of the crop's season type is used.
    """
    field = session.scalar(select(Field).where(Field.id == field_id, visible_to(user)))
    if field is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Field not found")
    try:
        return water_vault(session, field, crop, on, get_config())
    except VaultError as error:
        # The code is what the screen turns into a sentence in the user's language.
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"code": error.code, **error.details},
        ) from error
