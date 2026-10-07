from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from cvat.apps.engine.renderers import CVATAPIRenderer

from cvat.apps.engine.models import Task
from cvat.apps.engine.permissions import TaskPermission
from cvat.apps.iam.permissions import get_iam_context
from cvat.apps.test.counts import count_annotations_by_class, count_annotations_by_class_and_source
from cvat.apps.test.permissions import AnnotationAnalyticsPermission


def _analytics_error(request, *, status_code: int, title: str, message: str, task_id=None):
    return render(
        request,
        "test/analytics_error.html",
        {
            "status_code": status_code,
            "title": title,
            "message": message,
            "task_id": task_id,
        },
        status=status_code,
    )


def _can_view_task(request, task: Task) -> bool:
    perm = TaskPermission.create_scope_view(
        request, task, iam_context=get_iam_context(request, task)
    )
    return bool(perm.check_access().allow)


def analytics_page(request, pk: int):
    if not request.user.is_authenticated:
        return _analytics_error(
            request,
            status_code=401,
            title="Sign in required",
            message="Log in to CVAT, then open this analytics link again.",
            task_id=pk,
        )

    try:
        task = Task.objects.select_related("organization").get(pk=pk)
    except Task.DoesNotExist:
        return _analytics_error(
            request,
            status_code=404,
            title="Task not found",
            message=f"There is no task with id {pk}. It may have been deleted, or the URL is wrong.",
            task_id=pk,
        )
    except (TypeError, ValueError):
        return _analytics_error(
            request,
            status_code=404,
            title="Task not found",
            message="That analytics URL is not a valid task id.",
            task_id=pk,
        )

    if not _can_view_task(request, task):
        return _analytics_error(
            request,
            status_code=403,
            title="No access",
            message="You do not have permission to view analytics for this task.",
            task_id=pk,
        )

    return render(
        request,
        "test/analytics.html",
        {
            "task_id": task.id,
            "task_name": task.name,
            "project_id": task.project_id,
        },
    )


class TaskAnalyticsViewSet(viewsets.GenericViewSet):
    queryset = Task.objects.all()
    iam_permission_class = AnnotationAnalyticsPermission
    # This is a retrieve-style endpoint. CVAT's global list filters expect
    # search_fields / lookup_fields and crash get_object without them.
    filter_backends = []
    renderer_classes = [CVATAPIRenderer, JSONRenderer]

    def _payload(self, task: Task, request) -> dict:
        group_by = request.query_params.get("group_by")
        if group_by == "source":
            classes = count_annotations_by_class_and_source(task.id)
        else:
            classes = count_annotations_by_class(task.id)
        return {
            "task_id": task.id,
            "task_name": task.name,
            "project_id": task.project_id,
            "group_by": group_by if group_by == "source" else None,
            "classes": classes,
            "total": sum(item["count"] for item in classes),
        }

    @action(detail=True, methods=["get"], url_path="annotation-counts")
    def annotation_counts(self, request, pk=None):
        task = self.get_object()
        response = Response(self._payload(task, request))
        response["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response["Pragma"] = "no-cache"
        return response

