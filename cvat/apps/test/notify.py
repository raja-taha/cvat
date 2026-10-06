import json

import redis
from django.conf import settings

CHANNEL_PREFIX = "cvat.test.annotations."


def _client() -> redis.Redis:
    return redis.Redis(
        host=settings.REDIS_INMEM_SETTINGS["HOST"],
        port=int(settings.REDIS_INMEM_SETTINGS["PORT"]),
        db=int(settings.REDIS_INMEM_DATABASES.CACHE),
        password=settings.REDIS_INMEM_SETTINGS["PASSWORD"] or None,
    )


def channel_for_task(task_id: int) -> str:
    return f"{CHANNEL_PREFIX}{task_id}"


def publish_task_changed(task_id: int) -> None:
    payload = json.dumps({"type": "annotations_changed", "task_id": task_id})
    _client().publish(channel_for_task(task_id), payload)
