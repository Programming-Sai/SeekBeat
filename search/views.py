from django.http import JsonResponse
from .search_engine import SearchEngine
from django_ratelimit.decorators import ratelimit
from asgiref.sync import async_to_sync
import logging
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiExample

logger = logging.getLogger('seekbeat')
# logger.setLevel(logging.DEBUG)

# Check all handlers
# print(logger.handlers)
# logger.debug("Testing log output")





# Normal Search Testing endpoint + parameters = http://127.0.0.1:8000/search/?query=MAn%20of%20steel

# Bulk Search Testing enpoint + parameters = http://127.0.0.1:8000/search/bulk/?queries=Adele%20Hello,Coldplay%20Viva%20La%20Vida,Imagine%20Dragons%20Believer,https://www.youtube.com/shorts/XU70gQ1GY-I


engine = SearchEngine()



@extend_schema(
    summary="Search for Music Content",
    description="This endpoint allows users to search for a music video or audio using a variety of inputs\n. The `query` parameter can be a song title, artist name, a line of lyrics, or a direct YouTube link. Internally, the system processes the query using YouTube's search logic, returning structured data  about matching content, including metadata such as title, duration, channel name, thumbnails, and streaming links. Useful for streaming, downloading, or embedding songs within a music player interface.",
    parameters=[
        OpenApiParameter(
            name='query',
            description='Search term (e.g., song title, artist, YouTube link)',
            required=True,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY
        )
    ],
    examples=[
        OpenApiExample(
            name="Search by title",
            value={"query": "Imagine Dragons Believer"},
            summary="Searches YouTube using a song title."
        ),
        OpenApiExample(
            name="Search by link",
            value={"query": "https://www.youtube.com/watch?v=7wtfhZwyrcc"},
            summary="Searches for a specific YouTube video using its URL."
        ),
        OpenApiExample(
            name="Search by artist",
            value={"query": "Imagine Dragons"},
            summary="Returns top results for songs or videos related to the artist Imagine Dragons."
        ),
        OpenApiExample(
            name="Search by lyrics",
            value={"query": "I'ma say all the words inside my head"},
            summary="Finds songs based on a snippet of lyrics."
        ),
    ],
    methods=["GET"],
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiResponse(description="Missing or invalid query parameter"),
        429: OpenApiResponse(description="Rate limit exceeded"),
        500: OpenApiResponse(description="Internal server error"),
    },
    tags=["Search"]
)

@api_view(["GET"])
@ratelimit(key='ip', rate='25/m', block=True)
def search_view(request):
    logger.info("Received single search request from %s", request.META.get('REMOTE_ADDR'))  # 🔹 LOG HERE
    
    query = request.GET.get('query', None)
    if not query:
        logger.warning("No query parameter provided")  # 🔹 LOG HERE
        return Response({"error": "No query parameter provided."}, status=400)
    
    classified = engine.clean_and_classify_query(query)
    logger.debug("Classified query: %s", classified)  # 🔹 LOG HERE

    try:
        result = async_to_sync(engine.regular_search_with_yt_api)(classified)
        logger.info("Search completed for query=%s, returned %s items", classified['query'], len(result) if isinstance(result, list) else 'error')  # 🔹 LOG HERE

    except Exception as e:
        logger.exception("Search failed for query=%s", classified['query'])  # 🔹 LOG HERE
        return Response({"error": "Internal error"}, status=500)

    return Response(result)






@extend_schema(
    summary="Search for Music Content In Bulk",
    description=f"This endpoint allows you to search for multiple songs or YouTube videos at once using a comma-separated list of search terms. Each term in the list can be a song title, artist name, partial lyrics, or a full YouTube link. The system will process and return search results for all provided terms in a single response. This is useful for batch operations like playlist generation, mass metadata lookup, or prefetching. Only the first {engine.max_bulk_search} queries will be processed if more are provided. Extra spaces are trimmed.",
    parameters=[
        OpenApiParameter(
            name='queries',
            description=f'Comma-separated list of search terms or YouTube links. a maximum of {engine.max_bulk_search} would be processed.',
            required=True,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY
        )
    ],
    examples=[
        OpenApiExample(
            name="Basic Bulk Search",
            value={"queries": "Imagine Dragons Believer,Adele Hello"},
            summary="Two separate title-based searches"
        ),
        OpenApiExample(
            name="Mixed Input Types",
            value={"queries": "Coldplay Viva La Vida,https://www.youtube.com/watch?v=7wtfhZwyrcc"},
            summary="One search by title, one by link"
        ),
        OpenApiExample(
            name="Lyrics-based Bulk Search",
            value={"queries": "I’m in love with the shape of you,Hello from the other side"},
            summary="Search using partial lyrics"
        ),
        OpenApiExample(
            name=f"Too many queries (only first {engine.max_bulk_search} used)",
            value={"queries": "man of steel,believer,adele,https://youtu.be/zqBG6cZbSr4?list=RDGMEMQ1dJ7wXfLlqCjwV0xfSNbAVMvEvlZVhs090,elevation,eminem,shape of you,https://www.youtube.com/watch?v=Ah44UFg72Rs,despacito,numb,in the end,hallelujah,night changes,smoke on the water"},
            summary=f"Backend only uses the first {engine.max_bulk_search}"
        ),
    ],
    tags=["Search"],
    methods=["GET"],
    responses={
        200: OpenApiTypes.OBJECT,
        400: OpenApiResponse(description="No valid queries provided"),
        429: OpenApiResponse(description="Rate limit exceeded"),
        500: OpenApiResponse(description="Internal server error"),
    }
)
@api_view(["GET"])
@ratelimit(key='ip', rate='5/m', block=True)
def bulk_search_view(request):
    logger.info("Received bulk search request: %s", request.GET.get('queries'))  # 🔹 LOG HERE

    raw = request.GET.get("queries", "")
    terms = [engine.clean_and_classify_query(q.strip()) for q in raw.split(",") if q.strip()]
    logger.debug("Classified bulk terms: %s", terms)  # 🔹 LOG HERE

    if not terms:
        logger.warning("Bulk search: no valid queries provided")  # 🔹 LOG HERE
        return Response({"error": "No valid queries provided."}, status=400)

    try:
        results = async_to_sync(engine.bulk_search)(search_terms=terms)
        logger.info("Bulk search completed with %d terms", len(terms))  # 🔹 LOG HERE
    except Exception as e:
        logger.exception("Bulk search failed")  # 🔹 LOG HERE
        return Response({"error": "Internal error"}, status=500)

    return Response(results)