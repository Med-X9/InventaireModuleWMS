from django.urls import path

from apps.devices.views import DeviceHeartbeatView

urlpatterns = [
    path("heartbeat/", DeviceHeartbeatView.as_view(), name="device-heartbeat"),
]
