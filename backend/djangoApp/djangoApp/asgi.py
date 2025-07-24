"""
ASGI config for djangoApp project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

# djangoApp/asgi.py
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")

import ocr_app.routing
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from channels.sessions import SessionMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")
django_app = get_asgi_application()


async def debug_scope(scope, receive, send):
    print("▶ ASGI SCOPE:", scope)  # websocket인지 http인지, headers 등 전부 출력
    app = ProtocolTypeRouter(
        {
            "http": django_app,
            "websocket": SessionMiddlewareStack(
                URLRouter(ocr_app.routing.websocket_urlpatterns)
            ),
        }
    )
    await app(scope, receive, send)


application = debug_scope
