"""Reference lists the screens need, read from config/ so no key is repeated in the interface."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import require_roles
from app.core.parameters import get_config
from app.models import Role, User

router = APIRouter(prefix="/reference", tags=["reference"])

StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]


class SoilOut(BaseModel):
    key: str
    name_tr: str
    taw_mm_per_m: tuple[float, float]


@router.get("/soils", response_model=list[SoilOut])
def soils(_user: StaffUser) -> list[SoilOut]:
    """Soil textures a field can have (FAO-56 Table 19), with the water they hold."""
    return [
        SoilOut(key=key, name_tr=soil.name_tr, taw_mm_per_m=soil.taw_mm_per_m)
        for key, soil in get_config().soils.items()
    ]
