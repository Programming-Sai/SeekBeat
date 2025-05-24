from django.urls import path
from . import views

urlpatterns = [
    path("session-start/", views.start_lan_session_view, name="initiate session"),
    path("session-check/", views.check_lan_session_status, name="check session"),
    path("session-end/", views.terminate_lan_session, name="end session"),
    path("device-connect/", views.device_handshake_view, name="device connection"),
    path("device-disconnect/", views.device_disconnect_view, name="device disconnection"),
    path("devices/", views.active_devices_view, name="gets all active devices"),
]

