# djangoApp/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import streamapp.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")
django_asgi_app = get_asgi_application()


async def debug_scope(scope, receive, send):
    print("▶ ASGI SCOPE:", scope)  # websocket인지 http인지, headers 등 전부 출력
    app = ProtocolTypeRouter(
        {
            "http": django_asgi_app,
            # "websocket": SessionMiddlewareStack(
            #     URLRouter(ocr_app.routing.websocket_urlpatterns)
            # ),
            "websocket": URLRouter(streamapp.routing.websocket_urlpatterns),
        }
    )
    await app(scope, receive, send)


application = debug_scope
