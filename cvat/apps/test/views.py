from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from cvat.apps.engine.models import Task
from cvat.apps.test.counts import count_annotations_by_class, count_annotations_by_class_and_source
from cvat.apps.test.permissions import AnnotationAnalyticsPermission


class TaskAnalyticsViewSet(viewsets.GenericViewSet):
    queryset = Task.objects.all()
    iam_permission_class = AnnotationAnalyticsPermission
    # This is a retrieve-style endpoint. CVAT's global list filters expect
    # search_fields / lookup_fields and crash get_object without them.
    filter_backends = []

    def _payload(self, task: Task, request) -> dict:
        group_by = request.query_params.get("group_by")
        if group_by == "source":
            classes = count_annotations_by_class_and_source(task.id)
        else:
            classes = count_annotations_by_class(task.id)
        return {
            "task_id": task.id,
            "task_name": task.name,
            "group_by": group_by if group_by == "source" else None,
            "classes": classes,
            "total": sum(item["count"] for item in classes),
        }

    @action(detail=True, methods=["get"], url_path="annotation-counts")
    def annotation_counts(self, request, pk=None):
        task = self.get_object()
        return Response(self._payload(task, request))

    @action(detail=True, methods=["get"], url_path="analytics")
    def analytics(self, request, pk=None):
        task = self.get_object()
        return render(
            request,
            "test/analytics.html",
            {
                "task_id": task.id,
                "task_name": task.name,
            },
        )
