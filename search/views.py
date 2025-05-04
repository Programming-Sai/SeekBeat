from django.http import JsonResponse
from .search_engine import SearchEngine
from django_ratelimit.decorators import ratelimit
from asgiref.sync import async_to_sync



# Input validation, parameterization of max_results/limit/offset, and better error-handling.
# Detect links vs. terms in your search input.
# Logging for debugging and tracking failures.

# Caching strategy (frequency, result size, Redis integration).
# LAN search implementation (currently a stub).
# Frontend filter support (length, quality, date/view-count filters).






engine = SearchEngine()


@ratelimit(key='ip', rate='25/m', block=True)   
def search_view(request):
    query = request.GET.get('query', None)
    
    if query:
        query = engine.clean_and_classify_query(query)
        # result = await engine.regular_search(query)
        result = async_to_sync(engine.regular_search_with_yt_api)(query)
        print('query:', query)
        return JsonResponse(result, safe=False)
    return JsonResponse({"error": "No query parameter provided."}, status=400)





@ratelimit(key='ip', rate='5/m', block=True) 
def bulk_search_view(request):
    queries = request.GET.get("queries", "")
    terms = [engine.clean_and_classify_query(q.strip()) for q in queries.split(",") if q.strip()]
    print(terms)
    
    if not terms:
        return JsonResponse({"error": "No valid queries provided. Please provide comma-separated search terms."}, status=400)
    
    results = async_to_sync(engine.bulk_search)(search_terms=terms)

    return JsonResponse(results, safe=False)