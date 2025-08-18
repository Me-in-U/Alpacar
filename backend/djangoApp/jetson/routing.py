# jetson/routing.py
from django.urls import re_path
from .consumers import JetsonIngestConsumer, ParkingStatusConsumer

websocket_urlpatterns = [
    # Jetson -> Django
    re_path(r"^ws/jetson/$", JetsonIngestConsumer.as_asgi()),
    # Django -> Frontend
    re_path(r"^ws/parking_status$", ParkingStatusConsumer.as_asgi()),
]
