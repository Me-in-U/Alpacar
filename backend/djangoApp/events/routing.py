# events/routing.py
from django.urls import re_path
from .consumers import ParkingLogConsumer

websocket_urlpatterns = [
    re_path(r"ws/parking-logs/$", ParkingLogConsumer.as_asgi()),
]
