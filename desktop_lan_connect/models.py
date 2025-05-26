from django.db import models
import uuid

class DeviceProfile(models.Model):
    """
    Represents a device on the LAN that has joined the desktop-hosted session.
    Tracks basic system stats and participation status.
    """
    device_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    device_name = models.CharField(max_length=100, unique=True)
    os_version = models.CharField(max_length=50)
    ram_mb = models.IntegerField(null=True, blank=True)
    storage_mb = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    keep_data_on_leave = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.device_name} ({self.device_id})"


class SongProfile(models.Model):
    """
    Stores metadata about a song registered by a device. Each song is optionally
    linked to its source device.
    """
    song_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    device = models.ForeignKey(DeviceProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='songs')
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=200, blank=True, null=True)
    duration_seconds = models.IntegerField()
    file_size_kb = models.IntegerField()
    file_format = models.CharField(max_length=50)
    upload_timestamp = models.DateTimeField(auto_now_add=True)
    file_uploaded = models.BooleanField(default=False)
    file_path = models.CharField(max_length=500, null=True, blank=True) 
    port = models.IntegerField(default=8000)
    device_file_path = models.TextField(blank=True, null=True)


    def __str__(self):
        return f"{self.title} - {self.artist or 'Unknown'} - {self.device}"
