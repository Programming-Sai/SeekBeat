import uuid
from django.db import models



class BookmarkedVideo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    duration = models.PositiveIntegerField()  # in seconds
    uploader = models.CharField(max_length=255)
    thumbnail = models.URLField()
    webpage_url = models.URLField(unique=True)
    upload_date = models.CharField(max_length=8)  # e.g., "20240525"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title