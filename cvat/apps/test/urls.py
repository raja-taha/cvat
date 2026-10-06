from rest_framework import routers
from django.urls import include, path

from cvat.apps.test import views

router = routers.DefaultRouter(trailing_slash=False)
router.register("tasks", views.TaskAnalyticsViewSet, basename="test_task_analytics")

urlpatterns = [
    path("test/", include(router.urls)),
]
