from django.contrib import admin

from .models import BookmarkedVideo

@admin.register(BookmarkedVideo)
class BookmarkedVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploader', 'duration', 'upload_date', 'created_at')
    search_fields = ('title', 'uploader')
    ordering = ('-created_at',)