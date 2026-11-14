"""Everything under /api/v1. Routers are added here as their phases arrive."""

from fastapi import APIRouter

from app.api import auth

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
