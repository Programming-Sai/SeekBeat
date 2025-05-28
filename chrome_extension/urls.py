from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_all_bookmarks_view, name='bookmark-list'),         
    path('add', views.add_bookmark_view, name='add-bookmark'),         
    path('delete-all/', views.delete_all_bookmarks_view, name='bookmark-delete-all'),  
    path('<uuid:id>/', views.get_bookmark_view, name='bookmark-detail'),  
    path('<uuid:id>/delete/', views.delete_bookmark_view, name='bookmark-delete'),  
]
