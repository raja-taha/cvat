from django.apps import AppConfig


class TestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "cvat.apps.test"
    label = "annotation_test"
    verbose_name = "Annotation analytics (assessment)"

    def ready(self) -> None:
        from cvat.apps.test.hooks import install_annotation_hooks

        install_annotation_hooks()
