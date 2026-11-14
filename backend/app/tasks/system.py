"""Tasks that check the queue itself."""

from app.tasks.celery_app import celery_app


@celery_app.task(name="system.ping")
def ping() -> str:
    return "pong"
