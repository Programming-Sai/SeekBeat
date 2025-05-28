import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiTypes
from .bookmarks import BookMarkManager  # assuming your manager class is in managers.py
from .serializers import BookmarkedVideoSerializer

logger = logging.getLogger('seekbeat')

@extend_schema(
    summary="Add a new bookmarked video",
    description="Adds a YouTube video to bookmarks with metadata like title, uploader, duration, and thumbnail.",
    request=BookmarkedVideoSerializer,
    responses={
        201: BookmarkedVideoSerializer,
        400: OpenApiResponse(description="Invalid data – payload validation failed"),
        500: OpenApiResponse(description="Internal server error"),
    },
    tags=["Bookmarks"],
)
@api_view(["POST"])
def add_bookmark_view(request):
    logger.info("POST /bookmarks - Adding new bookmark")
    manager = BookMarkManager()
    try:
        result = manager.add_bookmark(request.data)
        if "error" in result:
            logger.warning(f"Bookmark addition failed: {result['error']}")
            return Response(result, status=400)
        logger.info(f"Bookmark successfully added: {result.get('title', 'unknown title')}")
        return Response(result, status=201)
    except Exception as e:
        logger.error(f"Unexpected error adding bookmark: {str(e)}")
        return Response({"error": "Internal server error"}, status=500)


@extend_schema(
    summary="Get all bookmarked videos",
    description="Returns a list of all bookmarked videos ordered by creation time (most recent first).",
    responses={
        200: BookmarkedVideoSerializer(many=True),
        500: OpenApiResponse(description="Internal server error"),
    },
    tags=["Bookmarks"],
)
@api_view(["GET"])
def get_all_bookmarks_view(request):
    logger.info("GET /bookmarks - Fetching all bookmarks")
    manager = BookMarkManager()
    try:
        result = manager.get_all_bookmarks()
        if "error" in result:
            logger.error(f"Error fetching bookmarks: {result['error']}")
            return Response(result, status=500)
        logger.info(f"Successfully fetched {len(result)} bookmarks")
        return Response(result)
    except Exception as e:
        logger.error(f"Unexpected error fetching bookmarks: {str(e)}")
        return Response({"error": "Internal server error"}, status=500)


@extend_schema(
    summary="Get a bookmarked video by ID",
    description="Returns metadata of a single bookmarked video by its UUID.",
    responses={
        200: BookmarkedVideoSerializer,
        404: OpenApiResponse(description="Bookmark not found"),
        500: OpenApiResponse(description="Internal server error"),
    },
    tags=["Bookmarks"],
)
@api_view(["GET"])
def get_bookmark_view(request, id):
    logger.info(f"GET /bookmarks/{id} - Fetching bookmark")
    manager = BookMarkManager()
    try:
        result = manager.get_bookmark(id)
        if "error" in result:
            logger.error(f"Error fetching bookmark {id}: {result['error']}")
            return Response(result, status=404)
        logger.info(f"Successfully fetched bookmark ID {id}: {result.get('title', 'unknown title')}")
        return Response(result)
    except Exception as e:
        logger.error(f"Unexpected error fetching bookmark {id}: {str(e)}")
        return Response({"error": "Internal server error"}, status=500)


@extend_schema(
    summary="Delete a bookmarked video by ID",
    description="Deletes a single bookmarked video using its UUID.",
    responses={
        200: OpenApiTypes.OBJECT,
        404: OpenApiResponse(description="Bookmark not found"),
        500: OpenApiResponse(description="Internal server error"),
    },
    tags=["Bookmarks"],
)
@api_view(["DELETE"])
def delete_bookmark_view(request, id):
    logger.info(f"DELETE /bookmarks/{id} - Attempting to delete bookmark")
    manager = BookMarkManager()
    try:
        result = manager.delete_bookmark(id)
        if "error" in result:
            logger.error(f"Error deleting bookmark {id}: {result['error']}")
            return Response(result, status=404)
        logger.info(f"Successfully deleted bookmark ID {id}")
        return Response(result)
    except Exception as e:
        logger.error(f"Unexpected error deleting bookmark {id}: {str(e)}")
        return Response({"error": "Internal server error"}, status=500)


@extend_schema(
    summary="Delete all bookmarked videos",
    description="Deletes all bookmarked videos from the database.",
    responses={
        200: OpenApiTypes.OBJECT,
        500: OpenApiResponse(description="Internal server error"),
    },
    tags=["Bookmarks"],
)
@api_view(["DELETE"])
def delete_all_bookmarks_view(request):
    logger.info("DELETE /bookmarks - Deleting all bookmarks")
    manager = BookMarkManager()
    try:
        result = manager.delete_all_bookmarks()
        if "error" in result:
            logger.error(f"Error deleting all bookmarks: {result['error']}")
            return Response(result, status=500)
        logger.info(f"Successfully deleted {result.get('deleted', 0)} bookmarks")
        return Response(result)
    except Exception as e:
        logger.error(f"Unexpected error deleting all bookmarks: {str(e)}")
        return Response({"error": "Internal server error"}, status=500)
