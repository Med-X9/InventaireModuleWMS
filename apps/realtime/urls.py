from django.urls import path

from apps.realtime.views.presence_views import ConnectedDevicesListView

app_name = "realtime"

urlpatterns = [
    path(
        "connected-devices/",
        ConnectedDevicesListView.as_view(),
        name="connected-devices",
    ),
]
