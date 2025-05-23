from django.contrib import admin
from .models import DeviceProfile, SongProfile

@admin.register(DeviceProfile)
class DeviceProfileAdmin(admin.ModelAdmin):
    list_display = ('device_name', 'device_id', 'is_active', 'last_seen', 'keep_data_on_leave')
    search_fields = ('device_name',)
    list_filter = ('is_active', 'keep_data_on_leave')

@admin.register(SongProfile)
class SongProfileAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'file_format', 'device', 'upload_timestamp')
    search_fields = ('title', 'artist')
    list_filter = ('file_format',)
