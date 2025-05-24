from django.urls import path
from . import views

urlpatterns = [
    path("session-start/", views.start_lan_session_view, name="initiate session"),
    path("session-check/", views.check_lan_session_status, name="check session"),
    path("session-end/", views.terminate_lan_session, name="end session"),
    path("device-connect/", views.device_handshake_view, name="device connection"),
    path("device-reconnect/", views.device_reconnect_view, name="device reconnection"),
    path("device-disconnect/", views.device_disconnect_view, name="device disconnection"),
    path("devices/", views.active_devices_view, name="gets all active devices"),
    path("device/<uuid:id>/songs", views.list_delete_device_songs_view, name="gets or deletes all songs for a given devices"),
    path("device/<uuid:device_id>/songs/bulk_add", views.bulk_add_songs_view, name="adds all songs for a given devices"),
    path("device/<uuid:device_id>/songs/<uuid:song_id>/upload", views.upload_song_file_view, name="uploads a song for a given devices"),
    path("device/<uuid:id>/songs/add", views.add_single_song_metadata, name="add a single song based on the current device"),
    path("device/<uuid:device_id>/songs/<uuid:song_id>", views.patch_delete_song_view, name="updates or deletes a single song based on the current device"),
]

