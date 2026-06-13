from django.urls import path

from apps.devices.views import DeviceStatusListView

urlpatterns = [
    path("status/", DeviceStatusListView.as_view(), name="device-status-list"),
]
