from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_view, name='search'),
    path("bulk/", views.bulk_search_view, name="bulk_search"),
]
