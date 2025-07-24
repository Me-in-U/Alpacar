# ocr_app/routing.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path

from . import ocr
from .consumers import OCRTextConsumer, OcrImageConsumer


# URL 매핑
websocket_urlpatterns = [
    re_path(r"^ws_text/?$", OCRTextConsumer.as_asgi()),
    re_path(r"^ws_ocr/?$", OcrImageConsumer.as_asgi()),
]
