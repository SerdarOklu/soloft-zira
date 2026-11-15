"""Everything under /api/v1. Routers are added here as their phases arrive."""

from fastapi import APIRouter

from app.api import (
    auth,
    dashboard,
    data_center,
    field_memory,
    fields,
    messages,
    reference,
    rotation,
    water_vault,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(reference.router)
api_router.include_router(fields.router)
api_router.include_router(field_memory.router)
api_router.include_router(water_vault.router)
api_router.include_router(rotation.router)
api_router.include_router(messages.router)
api_router.include_router(data_center.router)
api_router.include_router(dashboard.router)
