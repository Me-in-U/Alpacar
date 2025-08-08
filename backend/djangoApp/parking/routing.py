# app/routing.py
from django.urls import re_path

from parking.consumers import CarPositionConsumer, ParkingSpaceConsumer


websocket_urlpatterns = [
    re_path(r"ws/car-position/$", CarPositionConsumer.as_asgi()),
    re_path(r"ws/parking-space/$", ParkingSpaceConsumer.as_asgi()),
]
