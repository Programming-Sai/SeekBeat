from django.urls import path
from . import views

urlpatterns = [
    path("<str:video_url>/", views.stream_url_view, name="get_stream_url"),
]
