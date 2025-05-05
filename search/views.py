from django.http import JsonResponse
from .search_engine import SearchEngine
from django_ratelimit.decorators import ratelimit
from asgiref.sync import async_to_sync
import logging
logger = logging.getLogger('seekbeat')



# LAN search implementation (currently a stub).
# Tests
# Documentation



# Normal Search Testing endpoint + parameters = http://127.0.0.1:8000/search/?query=MAn%20of%20steel

# Bulk Search Testing enpoint + parameters = http://127.0.0.1:8000/search/bulk/?queries=Adele%20Hello,Coldplay%20Viva%20La%20Vida,Imagine%20Dragons%20Believer,https://www.youtube.com/shorts/XU70gQ1GY-I


engine = SearchEngine()


@ratelimit(key='ip', rate='25/m', block=True)   
def search_view(request):
    logger.info("Received single search request from %s", request.META.get('REMOTE_ADDR'))  # 🔹 LOG HERE
    
    query = request.GET.get('query', None)
    if not query:
        logger.warning("No query parameter provided")  # 🔹 LOG HERE
        return JsonResponse({"error": "No query parameter provided."}, status=400)
    
    classified = engine.clean_and_classify_query(query)
    logger.debug("Classified query: %s", classified)  # 🔹 LOG HERE

    try:
        result = async_to_sync(engine.regular_search_with_yt_api)(classified)
        logger.info("Search completed for query=%s, returned %s items", classified['query'], len(result) if isinstance(result, list) else 'error')  # 🔹 LOG HERE

    except Exception as e:
        logger.exception("Search failed for query=%s", classified['query'])  # 🔹 LOG HERE
        return JsonResponse({"error": "Internal error"}, status=500)

    return JsonResponse(result, safe=False)





@ratelimit(key='ip', rate='5/m', block=True) 
def bulk_search_view(request):
    logger.info("Received bulk search request: %s", request.GET.get('queries'))  # 🔹 LOG HERE

    raw = request.GET.get("queries", "")
    terms = [engine.clean_and_classify_query(q.strip()) for q in raw.split(",") if q.strip()]
    logger.debug("Classified bulk terms: %s", terms)  # 🔹 LOG HERE

    if not terms:
        logger.warning("Bulk search: no valid queries provided")  # 🔹 LOG HERE
        return JsonResponse({"error": "No valid queries provided."}, status=400)

    try:
        results = async_to_sync(engine.bulk_search)(search_terms=terms)
        logger.info("Bulk search completed with %d terms", len(terms))  # 🔹 LOG HERE
    except Exception as e:
        logger.exception("Bulk search failed")  # 🔹 LOG HERE
        return JsonResponse({"error": "Internal error"}, status=500)

    return JsonResponse(results, safe=False)