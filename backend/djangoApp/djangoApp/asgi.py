# djangoApp/asgi.py
"""
ASGI config for djangoApp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""
import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

import streamapp.routing

import logging

logger = logging.getLogger("channels")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")
django_asgi_app = get_asgi_application()


async def debug_scope(scope, receive, send):
    if scope["type"] == "http":
        logger.debug(f"HTTP 요청: {scope}")
    elif scope["type"] == "websocket":
        logger.debug(f"WebSocket 요청: {scope}")
    else:
        logger.debug(f"기타 요청 타입: {scope}")

    app = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            # "websocket": SessionMiddlewareStack(
            #     URLRouter(ocr_app.routing.websocket_urlpatterns)
            # ),
            "websocket": AuthMiddlewareStack(
                URLRouter(streamapp.routing.websocket_urlpatterns)
            ),
        }
    )
    await app(scope, receive, send)


application = debug_scope
