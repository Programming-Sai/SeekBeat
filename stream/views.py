# streaming/views.py

import logging
from django.http import StreamingHttpResponse, JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from django_ratelimit.decorators import ratelimit
from drf_spectacular.types import OpenApiTypes
from django.shortcuts import redirect, render
from .streaming_engine import StreamingEngine

logger = logging.getLogger('seekbeat')
handler = logging.getLogger('seekbeat').handlers[0]
handler.doRollover()

# logger.setLevel(logging.DEBUG)

# Check all handlers
# print(logger.handlers)
logger.debug("Testing log output")


engine = StreamingEngine()




@extend_schema(
    summary="Stream YouTube Audio",
    description="This endpoint extracts and returns a direct streamable audio URL from a YouTube link. "
                "The link must point to a valid individual video (not a playlist or mix). "
                "It is used to power frontend audio players or local streaming modules.",
    parameters=[
        OpenApiParameter(
            name='url',
            description='Direct YouTube video URL',
            required=True,
            type=str,
            location=OpenApiParameter.PATH
        ),
    ],
    examples=[
        OpenApiExample(
            name="Valid YouTube video link",
            value="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            summary="Returns stream URL for this video"
        )
    ],
    methods=["GET"],
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiResponse(description="Missing or invalid YouTube link"),
        500: OpenApiResponse(description="Extraction failed or internal error")
    },
    tags=["Streaming"]
)
@api_view(["GET", "POST"])
@ratelimit(key='ip', rate='30/m', block=True)
def stream_url_view(request, video_url):
    if request.method == "GET":
        logger.info("Stream request from %s for video_url=%s", request.META.get("REMOTE_ADDR"), video_url)

        if not video_url:
            logger.warning("Missing video URL in path")
            return Response({"error": "Missing YouTube video URL."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            full_url = f"https://www.youtube.com/watch?v={video_url}"
            data = engine.extract_stream_url(full_url)
            # data = engine.extract_stream_url(video_url)
            logger.info("Stream URL extracted successfully for %s", video_url)
            return Response(data)
        except Exception as e:
            logger.exception("Stream extraction failed for %s", video_url)
            return Response({"error": "Failed to extract stream URL."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == "POST":

        data = request.data
        video_url = data.get("url")
        edits = data.get("edits", {})

        if not video_url:
            return JsonResponse({"error": "Missing URL"}, status=400)

        try:
            stream = engine.stream_with_edits(video_url, edits)
            response = StreamingHttpResponse(stream, content_type="audio/mpeg")
            response["Content-Disposition"] = 'attachment; filename="edited_audio.mp3"'
            return response
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)



# http://localhost:8000/api/stream/vEvlZVhs090/





def stream_test_view(request):
    # title = request.GET.get('title')
    stream_url = request.GET.get('id')
    stream_info = engine.extract_stream_url(stream_url)
    return redirect(stream_info["stream_url"])
    # return render(request, 'streaming/test_player.html', {'stream_url': stream_url, 'title': title})


# http://localhost:8000/api/stream/test/?id=dQw4w9WgXcQ



