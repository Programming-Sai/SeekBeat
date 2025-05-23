from django.urls import path
from . import views

urlpatterns = [
    path("session-start/", views.start_lan_session_view, name="initiate session"),
    path("session-check/", views.check_lan_session_status, name="check session"),
    path("session-end/", views.terminate_lan_session, name="end session"),
]

