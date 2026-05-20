"""
ASGI pour HTTP (Django) + WebSocket (Django Channels).

Développement / production WebSocket :
    daphne -b 0.0.0.0 -p 8000 project.asgi:application

Le serveur HTTP classique ``gunicorn project.wsgi`` ne gère pas les WebSockets.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from apps.realtime.middleware.jwt_websocket_auth import JWTAuthMiddlewareStack
from apps.realtime.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
    }
)
