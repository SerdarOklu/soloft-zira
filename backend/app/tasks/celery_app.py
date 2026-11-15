"""Celery application. Slow work (NASA fetches, 25-season runs) runs here, never in a request."""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "zira",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.system",
        "app.tasks.power",
        "app.tasks.modis",
        "app.tasks.landsat",
        "app.tasks.terrain",
    ],
)
celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
    task_track_started=True,
    # One job at a time per worker process: the VPS has 2 shared vCPUs.
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    timezone="UTC",
)
