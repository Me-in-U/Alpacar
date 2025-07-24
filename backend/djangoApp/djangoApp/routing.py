import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import ocr_app.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoApp.settings")
django_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_app,
        "websocket": AllowedHostsOriginValidator(
            SessionMiddlewareStack(URLRouter(ocr_app.routing.websocket_urlpatterns))
        ),
    }
)
