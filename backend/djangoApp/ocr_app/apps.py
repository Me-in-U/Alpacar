# ocr_app/apps.py
import sys
from django.apps import AppConfig


class OcrAppConfig(AppConfig):
    name = "ocr_app"

    def ready(self):
        from .ocr import start_capture

        start_capture()
        if len(sys.argv) >= 2 and sys.argv[1] == "runserver":
            from .ocr import start_capture

            start_capture()
