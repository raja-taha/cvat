from cvat.apps.engine.permissions import TaskPermission


class AnnotationAnalyticsPermission(TaskPermission):
    """Reuse CVAT task view rules. Any action on this app is a task VIEW check."""

    @classmethod
    def _get_scopes(cls, request, view, obj):
        return [cls.Scopes.VIEW]
