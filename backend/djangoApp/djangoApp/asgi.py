# djangoApp/asgi.py

"""
ASGI config for djangoApp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""
import os

# settings 모듈 지정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")

# Django 앱 초기화
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

# 로깅 설정
import logging

import events.routing

# 라우팅 설정
import streamapp.routing

# Channels import (이제 models, apps 모두 로드된 이후)
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

import jetson.routing

logger = logging.getLogger("channels")


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
                URLRouter(
                    streamapp.routing.websocket_urlpatterns
                    + events.routing.websocket_urlpatterns
                    + jetson.routing.websocket_urlpatterns
                )
            ),
        }
    )
    await app(scope, receive, send)


application = debug_scope
