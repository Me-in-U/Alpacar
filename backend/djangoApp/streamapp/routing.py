from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # 라즈베리파이가 업로드할 WebSocket 엔드포인트
    re_path(r"ws/upload/$", consumers.PiUploadConsumer.as_asgi()),
    # 관리자 대시보드용 실시간 스트림 엔드포인트
    re_path(r"ws/stream/$", consumers.StreamConsumer.as_asgi()),
    # OCR 번호판 결과
    re_path(r"ws/text/$", consumers.OCRTextConsumer.as_asgi()),
]
