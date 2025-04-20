from django.http import JsonResponse
# from .search_engine import SearchEngine
from .search_engine import SearchEngine


engine = SearchEngine()

def search_view(request):
    query = request.GET.get('query', None)
    
    if query:
        result = engine.regular_search(query)
        return JsonResponse(result, safe=False)
    return JsonResponse({"error": "No query parameter provided."})


def bulk_search_view(request):
    queries = request.GET.get("queries", "")
    terms = [q.strip() for q in queries.split(",") if q.strip()]
    
    if not terms:
        return JsonResponse({"error": "No queries provided"}, status=400)
    
    results = engine.bulk_search(search_terms=terms)

    return JsonResponse(results, safe=False)