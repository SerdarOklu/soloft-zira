"""SMAP, GPM IMERG and GRACE fetch jobs. They run in the worker, never inside a request."""

import uuid

from sqlalchemy.orm import Session

from app.core.db import get_engine
from app.services.regional import run_fetch_job
from app.tasks.celery_app import celery_app


@celery_app.task(name="regional.fetch_field_regional")
def fetch_field_regional(job_id: str) -> str:
    with Session(get_engine()) as session:
        job = run_fetch_job(session, uuid.UUID(job_id))
        return job.status.value
