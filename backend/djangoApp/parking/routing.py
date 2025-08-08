# app/routing.py
from django.urls import re_path

from parking.consumers import CarPositionConsumer


websocket_urlpatterns = [
    re_path(r"ws/car-position/$", CarPositionConsumer.as_asgi()),
]
