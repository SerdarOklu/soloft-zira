"""Everything under /api/v1. Routers are added here as their phases arrive."""

from fastapi import APIRouter

from app.api import auth, dashboard, data_center, fields

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(fields.router)
api_router.include_router(data_center.router)
api_router.include_router(dashboard.router)
