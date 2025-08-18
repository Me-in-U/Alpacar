# events/apps.py
from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"

    def ready(self):
        # signals 모듈을 import 해야 receiver들이 연결됩니다.
        from . import signals  # noqa
