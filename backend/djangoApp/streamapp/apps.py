from django.apps import AppConfig


class StreamappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "streamapp"

    def ready(self):
        # 시그널 등록
        from . import signals  # noqa
