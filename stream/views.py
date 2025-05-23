# streaming/views.py

import json
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
    description=(
        "GET returns stream metadata; POST streams edited audio. "
        "Provide `edits` JSON with speed, trim, volume, metadata fields."
    ),
    parameters=[
        OpenApiParameter(
            name='video_url',
            description='YouTube ID',
            required=True,
            type=str,
            location=OpenApiParameter.PATH
        ),
    ],
    request=OpenApiTypes.OBJECT,
    responses={
        200: OpenApiResponse(
            description="Stream metadata JSON or audio/mpeg stream",
        ),
        400: OpenApiResponse(description="Invalid request data"),
        500: OpenApiResponse(description="Internal server error")
    },
    methods=["GET", "POST"],
    tags=["Streaming"],
    examples=[
        OpenApiExample(
            name="Fetch Stream URL (GET)",
            summary="Successful GET response",
            value={"stream_url": "...", "title": "...", "duration": 123, "thumbnail": "..."},
            response_only=True,
            request_only=False
        ),
        OpenApiExample(
            name="Edited Stream (POST)",
            summary="Example edits payload",
            value={
                "edits": {
                    "speed": 1.25,
                    "trim": {"start_time": 10, "end_time": 120},
                    "volume": 0.5,
                    "metadata": {
                        "title": "The High Seas' Anthem",
                        "artist": "Pirate Sea Shanty - Topic",
                        "album": "Sea Shanties Vol.1",
                        "date": "2025-05-19",
                        "genre": "Folk",
                        "url": "https://youtu.be/V_N1MavsGJE",
                        "thumbnail": "https://i.ytimg.com/vi_webp/V_N1MavsGJE/maxresdefault.webp"
                    }
                }
            },
            request_only=True,
            response_only=False
        ),
        OpenApiExample(
            name="No Edits Stream (POST)",
            summary="Example empty edits payload (for normal downloads)",
            value={
                "edits": {}
            },
            request_only=True,
            response_only=False
        )
    ]
)
@api_view(["GET", "POST"])
@ratelimit(key='ip', rate='30/m', block=True)
def stream_url_view(request, video_url):
    if not video_url:
        logger.warning("Missing video URL in path")
        return Response({"error": "Missing YouTube video URL."}, status=status.HTTP_400_BAD_REQUEST)
    

    if request.method == "GET":
        logger.info("Stream request from %s for video_url=%s", request.META.get("REMOTE_ADDR"), video_url)

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
        raw_edits = request.data.get("edits", "{}")

        if isinstance(raw_edits, str):
            edits = json.loads(raw_edits)
        else:
            edits = raw_edits  # already a dict (like when using Postman or API clients)

        try:
            full_url = f"https://www.youtube.com/watch?v={video_url}"
            info = engine.extract_stream_url(video_url)
            input_src = info["stream_url"]
            duration = info["duration"]
            title = info["title"]
            stream = engine.stream_with_edits(input_src, edits, duration)
            response = StreamingHttpResponse(stream, content_type="audio/mpeg")
            response["Content-Disposition"] = f'attachment; filename="{title}.mp3"'
            return response
        except Exception as e:
            print(str(e))
            return JsonResponse({"error": str(e)}, status=500)



# http://localhost:8000/api/stream/vEvlZVhs090/




def stream_test_view(request):
    # title = request.GET.get('title')
    stream_url = request.GET.get('id')
    stream_info = engine.extract_stream_url(stream_url)
    return redirect(stream_info["stream_url"])
    # return render(request, 'streaming/test_player.html', {'stream_url': stream_url, 'title': title})


# http://localhost:8000/api/stream/test/?id=dQw4w9WgXcQ



