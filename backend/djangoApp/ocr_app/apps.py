# ocr_app/apps.py
import sys
from django.apps import AppConfig


class OcrAppConfig(AppConfig):
    name = "ocr_app"

    def ready(self):
        def ready(self):
            # 더 이상 여기서 start_capture를 직접 호출하지 않습니다.
            pass
