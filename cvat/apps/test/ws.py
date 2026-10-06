import asyncio
import logging
import re
from http.cookies import SimpleCookie

import redis.asyncio as redis_async
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.db import close_old_connections
from django.test import RequestFactory

from cvat.apps.test.notify import channel_for_task

logger = logging.getLogger(__name__)
TASK_WS_PATH = re.compile(r"^/api/test/tasks/(?P<task_id>\d+)/ws$")


def _user_from_scope(scope) -> object | None:
    headers = {key.decode(): value.decode() for key, value in scope.get("headers", [])}
    cookie = SimpleCookie()
    cookie.load(headers.get("cookie", ""))
    morsel = cookie.get(settings.SESSION_COOKIE_NAME)
    if not morsel or not morsel.value:
        return None
    session = SessionStore(session_key=morsel.value)
    user_id = session.get("_auth_user_id")
    if not user_id:
        return None
    User = get_user_model()
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None


def _can_view_task(user, task_id: int) -> bool:
    from cvat.apps.engine.models import Task
    from cvat.apps.engine.permissions import TaskPermission
    from cvat.apps.iam.middleware import get_organization
    from cvat.apps.iam.permissions import get_iam_context

    close_old_connections()
    try:
        task = Task.objects.select_related("organization").get(pk=task_id)
    except Task.DoesNotExist:
        return False
    request = RequestFactory().get(f"/api/test/tasks/{task_id}/ws")
    request.user = user
    request.iam_context = get_organization(request)
    perm = TaskPermission.create_scope_view(request, task, iam_context=get_iam_context(request, task))
    return bool(perm.check_access().allow)


async def handle_websocket(scope, receive, send) -> None:
    match = TASK_WS_PATH.match(scope.get("path") or "")
    if not match:
        await send({"type": "websocket.close", "code": 4404})
        return

    task_id = int(match.group("task_id"))
    connect = await receive()
    if connect["type"] != "websocket.connect":
        await send({"type": "websocket.close", "code": 4400})
        return

    user = await sync_to_async(_user_from_scope, thread_sensitive=True)(scope)
    if user is None:
        await send({"type": "websocket.close", "code": 4401})
        return
    allowed = await sync_to_async(_can_view_task, thread_sensitive=True)(user, task_id)
    if not allowed:
        await send({"type": "websocket.close", "code": 4403})
        return

    await send({"type": "websocket.accept"})
    await send(
        {
            "type": "websocket.send",
            "text": '{"type":"connected"}',
        }
    )

    client = redis_async.Redis(
        host=settings.REDIS_INMEM_SETTINGS["HOST"],
        port=int(settings.REDIS_INMEM_SETTINGS["PORT"]),
        db=int(settings.REDIS_INMEM_DATABASES.CACHE),
        password=settings.REDIS_INMEM_SETTINGS["PASSWORD"] or None,
    )
    pubsub = client.pubsub()
    await pubsub.subscribe(channel_for_task(task_id))
    stop = asyncio.Event()

    async def listen_socket() -> None:
        while True:
            event = await receive()
            if event["type"] in {"websocket.disconnect", "websocket.close"}:
                stop.set()
                return

    async def listen_redis() -> None:
        try:
            idle = 0.0
            while not stop.is_set():
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("type") == "message":
                    data = message.get("data")
                    text = data.decode() if isinstance(data, bytes) else str(data)
                    await send({"type": "websocket.send", "text": text})
                    idle = 0.0
                else:
                    idle += 1.0
                    if idle >= 20:
                        await send({"type": "websocket.send", "text": '{"type":"ping"}'})
                        idle = 0.0
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("annotation analytics websocket redis loop failed")
            stop.set()

    try:
        await asyncio.gather(listen_socket(), listen_redis())
    finally:
        stop.set()
        await pubsub.unsubscribe()
        await pubsub.aclose()
        await client.aclose()


def wrap_asgi(django_asgi):
    async def application(scope, receive, send):
        if scope["type"] == "websocket":
            await handle_websocket(scope, receive, send)
            return
        await django_asgi(scope, receive, send)

    return application
