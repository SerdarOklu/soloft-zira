"""The queue: the task is registered, runs inline, and runs through Redis with a worker."""

import pytest
import redis
from celery.contrib.testing.worker import start_worker

from app.core.config import get_settings
from app.tasks.celery_app import celery_app
from app.tasks.system import ping


def test_ping_task_is_registered_and_runs_inline():
    assert "system.ping" in celery_app.tasks
    assert ping.apply().get() == "pong"


@pytest.mark.queue
def test_ping_goes_through_the_broker_to_a_worker():
    try:
        redis.Redis.from_url(get_settings().redis_url, socket_connect_timeout=1).ping()
    except redis.exceptions.RedisError:
        pytest.skip("Redis is not reachable; start it to run queue tests")

    with start_worker(celery_app, perform_ping_check=False, pool="solo"):
        assert ping.delay().get(timeout=20) == "pong"
