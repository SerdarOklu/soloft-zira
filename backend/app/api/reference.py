"""Reference lists the screens need, read from config/ so no key is repeated in the interface."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import require_roles
from app.core.parameters import get_config
from app.models import Role, User
from app.schemas.water import CropOption
from app.services.water.vault import crop_options

router = APIRouter(prefix="/reference", tags=["reference"])

StaffUser = Annotated[
    User, Depends(require_roles(Role.ADMIN, Role.AGRONOMIST, Role.COOPERATIVE_USER))
]


class SoilOut(BaseModel):
    key: str
    name_tr: str
    taw_mm_per_m: tuple[float, float]


@router.get("/crops", response_model=list[CropOption])
def crops(_user: StaffUser) -> list[CropOption]:
    """The crops of config/crops.yaml, and whether their season can be run yet."""
    return crop_options(get_config())


@router.get("/soils", response_model=list[SoilOut])
def soils(_user: StaffUser) -> list[SoilOut]:
    """Soil textures a field can have (FAO-56 Table 19), with the water they hold."""
    return [
        SoilOut(key=key, name_tr=soil.name_tr, taw_mm_per_m=soil.taw_mm_per_m)
        for key, soil in get_config().soils.items()
    ]
