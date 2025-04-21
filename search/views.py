from django.http import JsonResponse
from .search_engine import SearchEngine


# TODO: Add proper input validation for search terms (e.g., ensure they are non-empty and valid).
# TODO: Parameterize max_results, limit, and offset values in search functions.
# TODO: Implement pagination for search results to handle larger result sets.
# TODO: Add functionality for handling errors in a more user-friendly way (e.g., specific error codes or messages).
# TODO: Add logging for better debugging and error tracking (e.g., log failed searches or unexpected results).
# TODO: Optimize performance by limiting the number of retries and the delay before retrying requests in case of failure.
# TODO: Add the option to filter search results based on video length (e.g., short or long videos).
# TODO: Improve the LAN-based search functionality (currently a placeholder).
# TODO: Consider using caching for frequently searched queries to improve performance (e.g., Redis).
# TODO: Handle the case when a search term returns no results with a more meaningful response (e.g., "No results found").
# TODO: Implement a rate-limiting mechanism to prevent excessive requests to YouTube's API and avoid being blocked.
# TODO: Add the ability to filter search results by video quality or resolution (e.g., 720p, 1080p).
# TODO: Test the performance of bulk searches to ensure the system scales with a large number of queries.
# TODO: Integrate additional search parameters, such as filtering by video upload date or view count.
# TODO: Improve error handling in the async search functions for better fault tolerance.
# TODO: Add a user feedback mechanism to allow users to report errors or issues with search results.



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