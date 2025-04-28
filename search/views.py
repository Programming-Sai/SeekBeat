from django.http import JsonResponse
from .search_engine import SearchEngine
 

 
# Obtain & configure your two YouTube API keys (one for normal searches, one for bulk).

# Integrate those keys into new async search functions (replacing yt-dlp for metadata).

# Add quota-usage checks so we know when to fall back to scraping.

# Input validation, parameterization of max_results/limit/offset, and better error-handling.

# Logging for debugging and tracking failures.

# LAN search implementation (currently a stub).

# Performance testing of bulk searches.

# Detect links vs. terms in your search input.

# Frontend filter support (length, quality, date/view-count filters).

# Caching strategy (frequency, result size, Redis integration).

# Rate-limit outbound scraping (for when we fall back to yt-dlp).




engine = SearchEngine()

async def search_view(request):
    query = request.GET.get('query', None)
    
    if query:
        # result = await engine.regular_search(query)
        result = await engine.regular_search_with_yt_api(query)
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