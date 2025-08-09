# events/apps.py
from django.apps import AppConfig


class EventsConfig(AppConfig):
    name = "events"

    def ready(self):
        import events.signals  # 시그널 등록
