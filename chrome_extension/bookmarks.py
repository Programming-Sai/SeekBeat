import logging
from .models import BookmarkedVideo
from .serializers import BookmarkedVideoSerializer
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from django.db import DatabaseError


logger = logging.getLogger('seekbeat')




class BookMarkManager:
    def get_all_bookmarks(self):
        logger.debug("Fetching all bookmarks...")
        try:
            bookmarks = BookmarkedVideo.objects.all().order_by('-created_at')
            logger.info(f"Fetched {bookmarks.count()} bookmarks.")
            return BookmarkedVideoSerializer(bookmarks, many=True).data
        except DatabaseError as e:
            logger.error(f"Database error while fetching bookmarks: {str(e)}")
            return {"error": "Failed to fetch bookmarks."}

    def delete_all_bookmarks(self):
        logger.debug("Attempting to delete all bookmarks...")
        try:
            count, _ = BookmarkedVideo.objects.all().delete()
            logger.info(f"Deleted {count} bookmarks.")
            return {"deleted": count}
        except DatabaseError as e:
            logger.error(f"Database error while deleting bookmarks: {str(e)}")
            return {"error": f"Failed to delete bookmarks: {str(e)}"}

    def delete_bookmark(self, id):
        logger.debug(f"Attempting to delete bookmark with ID: {id}")
        try:
            bookmark = get_object_or_404(BookmarkedVideo, id=id)
            bookmark.delete()
            logger.info(f"Deleted bookmark: {bookmark.title} (ID: {id})")
            return {"deleted": True}
        except Exception as e:
            logger.error(f"Failed to delete bookmark ID {id}: {str(e)}")
            return {"error": f"Bookmark not found or could not be deleted: {str(e)}"}

    def get_bookmark(self, id):
        logger.debug(f"Fetching bookmark with ID: {id}")
        try:
            bookmark = get_object_or_404(BookmarkedVideo, id=id)
            logger.info(f"Fetched bookmark: {bookmark.title} (ID: {id})")
            return BookmarkedVideoSerializer(bookmark).data
        except Exception as e:
            logger.error(f"Failed to fetch bookmark ID {id}: {str(e)}")
            return {"error": f"Bookmark not found: {str(e)}"}

    def add_bookmark(self, data):
        logger.debug(f"Received data for new bookmark: {data}")
        try:
            serializer = BookmarkedVideoSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save()
            logger.info(f"Bookmark added: {instance.title}")
            return serializer.data
        except ValidationError as e:
            logger.warning(f"Validation failed for bookmark: {e.detail}")
            return {"error": e.detail}
        except Exception as e:
            logger.error(f"Error adding bookmark: {str(e)}")
            return {"error": f"Failed to add bookmark: {str(e)}"}
