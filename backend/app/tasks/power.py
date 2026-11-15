"""NASA POWER fetch job. It runs in the worker, never inside a request."""

import uuid

from sqlalchemy.orm import Session

from app.core.db import get_engine
from app.core.parameters import get_config
from app.services.power import run_fetch_job
from app.tasks.celery_app import celery_app


@celery_app.task(name="power.fetch_field_weather")
def fetch_field_weather(job_id: str, force: bool = False) -> str:
    with Session(get_engine()) as session:
        job = run_fetch_job(session, uuid.UUID(job_id), get_config(), force=force)
        return job.status.value
