from django.http import JsonResponse
from .search_engine import SearchEngine
 

# TODO: Add proper input validation for search terms (e.g., ensure they are non-empty and valid).
# TODO: Parameterize max_results, limit, and offset values in search functions.
# TODO: Add functionality for handling errors in a more user-friendly way (e.g., specific error codes or messages).
# TODO: Add logging for better debugging and error tracking (e.g., log failed searches or unexpected results).
# TODO: Improve the LAN-based search functionality (currently a placeholder).
# TODO: Test the performance of bulk searches to ensure the system scales with a large number of queries.
# TODO: Add a way to determine if a link was provided or a serach term.
# FIlters
# TODO: Add the option to filter search results based on video length (e.g., short or long videos).
# TODO: Add the ability to filter search results by video quality or resolution (e.g., 720p, 1080p).
# TODO: Integrate additional search parameters, such as filtering by video upload date or view count.


## How often do we cache (on every search or what?)
## how many of the results should be cached since we can't cache everything all the time.



# A. Implement Redis caching of search results
# E. Apply rate-limiting on outbound scraping requests






engine = SearchEngine()

async def search_view(request):
    query = request.GET.get('query', None)
    
    if query:
        result = await engine.regular_search(query)
        print('query:', query)
        return JsonResponse(result, safe=False)
    return JsonResponse({"error": "No query parameter provided."})




async def bulk_search_view(request):
    queries = request.GET.get("queries", "")
    terms = [q.strip() for q in queries.split(",") if q.strip()]
    
    if not terms:
        return JsonResponse({"error": "No valid queries provided. Please provide comma-separated search terms."}, status=400)
    
    results = await engine.bulk_search(search_terms=terms)

    return JsonResponse(results, safe=False)