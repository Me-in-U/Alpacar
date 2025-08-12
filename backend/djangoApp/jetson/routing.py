# jetson/routing.py
from django.urls import re_path
from .consumers import JetsonAssignConsumer

websocket_urlpatterns = [
    re_path(r"ws/jetson/$", JetsonAssignConsumer.as_asgi()),
]
