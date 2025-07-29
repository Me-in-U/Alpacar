# djangoApp\routing.py
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import SessionMiddlewareStack
from django.core.asgi import get_asgi_application

import streamapp.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")
django_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_app,
        "websocket": AllowedHostsOriginValidator(
            SessionMiddlewareStack(URLRouter(streamapp.routing.websocket_urlpatterns))
        ),
    }
)
