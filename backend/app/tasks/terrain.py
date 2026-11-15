"""Terrain (SRTM / NASADEM) fetch job. It runs in the worker, never inside a request."""

import uuid

from sqlalchemy.orm import Session

from app.core.db import get_engine
from app.services.terrain import run_fetch_job
from app.tasks.celery_app import celery_app


@celery_app.task(name="terrain.fetch_field_terrain")
def fetch_field_terrain(job_id: str) -> str:
    with Session(get_engine()) as session:
        job = run_fetch_job(session, uuid.UUID(job_id))
        return job.status.value
