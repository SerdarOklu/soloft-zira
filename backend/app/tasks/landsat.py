"""Landsat NDVI fetch job. It runs in the worker, never inside a request."""

import uuid

from sqlalchemy.orm import Session

from app.core.db import get_engine
from app.services.landsat import run_fetch_job
from app.tasks.celery_app import celery_app


@celery_app.task(name="landsat.fetch_field_ndvi")
def fetch_field_ndvi(job_id: str) -> str:
    with Session(get_engine()) as session:
        job = run_fetch_job(session, uuid.UUID(job_id))
        return job.status.value
