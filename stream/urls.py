from django.urls import path
from . import views

urlpatterns = [
    path("test/", views.stream_test_view, name="stream-test"),
    path("<str:video_url>/", views.stream_url_view, name="get_stream_url"),
]

