from django.urls import path

from apps.realtime.consumers.dashboard_presence_consumer import (
    DashboardPresenceConsumer,
)
from apps.realtime.consumers.mobile_presence_consumer import MobilePresenceConsumer

websocket_urlpatterns = [
    path("ws/presence/mobile/", MobilePresenceConsumer.as_asgi()),
    path("ws/presence/dashboard/", DashboardPresenceConsumer.as_asgi()),
]
