# streamapp\routing.py
from django.urls import path, re_path

from streamapp.consumers import (
    OCRTextConsumer,
    PiUploadConsumer,
    PlateDisplayConsumer,
    StreamConsumer,
)

# WebSocket 엔드포인트
websocket_urlpatterns = [
    # 라즈베리파이가 이미지/텍스트 업로드용 WebSocket 엔드포인트
    path("ws/upload/", PiUploadConsumer.as_asgi()),
    # 관리자 대시보드용 실시간 스트림 엔드포인트
    path("ws/stream/", StreamConsumer.as_asgi()),
    # OCR 번호판 텍스트 전용 WebSocket 엔드포인트
    path("ws/text/", OCRTextConsumer.as_asgi()),
    re_path(r"^ws/platedisplay/?$", PlateDisplayConsumer.as_asgi()),
]
