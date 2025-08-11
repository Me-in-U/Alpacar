# events/apps.py
from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"

    def ready(self):
        # 시그널 연결
        import events.signals  # noqa
