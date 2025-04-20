import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed


class SearchEngine:
    """
    SearchEngine centralizes all search-related functionality:
      - regular_search: YouTube-based metadata search via yt-dlp
      - bulk_search: run multiple regular_search calls concurrently
      - lan_search: placeholder for LAN-based media search (future)
    """

    def __init__(self, config=None):
        """
        Initialize the SearchEngine with optional custom yt-dlp config.

        Args:
            config (dict, optional): A dict of yt-dlp options. If None,
                                     defaults to SEARCH_YDL_OPTS.
        """
        # Default yt-dlp options optimized for fast, metadata-only searches
        self.SEARCH_YDL_OPTS = {
            "format": "bestaudio/best",    # Best audio quality
            "noplaylist": True,              # Ignore playlists
            "quiet": True,                   # Suppress console output
            "skip_download": True,           # Do not download files
            "extract_flat": False,           # Get full metadata, not flat URLs
            "default_search": "ytsearch",  # Allows plain terms as search
            "source_address": "0.0.0.0",   # Avoid IPv6 resolution issues
            "cachedir": False,               # Disable yt-dlp cache
            "no_warnings": True,             # Suppress warnings
        }

        # Use provided config, or fall back to defaults
        self.config = config if config else self.SEARCH_YDL_OPTS
        # Initialize the yt-dlp extractor
        self.ydl = yt_dlp.YoutubeDL(self.config)
        # Default maximum number of results per query
        self.max_results = 10

    def regular_search(self, search_term:str, max_results: int=None, offset: int=None) -> list[dict]:
        """
        Perform a single metadata search on YouTube.

        Args:
            search_term (str): The query string or URL.
            max_results (int, optional): Limit of results to return.
                                         Defaults to self.max_results.
            offset (int, optional): Skip this many initial results.

        Returns:
            list[dict] or dict: A list of metadata dicts for matching videos,
                                 or an error dict on failure.
        """
        if not search_term:
            return {"error": "No search term provided"}

        try:
            limit = max_results or self.max_results
            total_to_fetch = limit + (offset or 0)

            # Use yt-dlp to fetch metadata for top `total_to_fetch` matches
            query = f"ytsearch{total_to_fetch}:{search_term}"
            result = self.ydl.extract_info(query, download=False)

            # if not result:
                # return {"error": f"No results found for '{search_term}'"} 

            # If it returns a playlist, slice out the desired window
            if isinstance(result, dict) and result.get("_type") == "playlist":
                entries = result.get("entries", [])
                return entries[offset or 0 : total_to_fetch]

            # Single video fallback
            return [result]

        except Exception as e:
            # Return a structured error to the API layer
            return {"error": f"An error occurred: {str(e)}"}

    def bulk_search(self, search_terms: str, max_results_per_term: int =5) -> list[dict]:
        """
        Perform concurrent searches for multiple terms.

        Args:
            search_terms (list[str]): List of query strings.
            max_results_per_term (int): Max results per term.

        Returns:
            list[dict]: A list of dicts, each containing:
                {
                  'search_term': original term,
                  'results': list of metadata dicts,
                  'count': number of results returned,
                  'error': optional error message
                }
        """
        if not search_terms:
            return [{"error": "No search terms provided"}]

        results = []
        # Use ThreadPoolExecutor to run multiple searches at once
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Map each Future to its search term for tracking
            future_to_term = {
                executor.submit(self.regular_search, term, max_results_per_term): term
                for term in search_terms
            }

            # As each search completes, build the result entry
            for future in as_completed(future_to_term):
                term = future_to_term[future]
                try:
                    data = future.result()
                    results.append({
                        'search_term': term,
                        'results': data,
                        'count': len(data) if isinstance(data, list) else 0
                    })
                except Exception as e:
                    # Capture any unexpected exceptions
                    results.append({
                        'search_term': term,
                        'error': str(e),
                        'count': 0
                    })
        return results
    

    def lan_search(self, search_term: str, scope: str = "all") -> list[dict]:
        """
        Placeholder for LAN-based search.

        Args:
            search_term (str): The term to look up in the LAN song database.
            scope (str):   Optional scope filter—e.g. "all" | "local" | "remote".
                           (“all” returns every matching device; “local” only this server;
                           “remote” only other nodes.)

        Returns:
            List[dict]: A list of result objects, each with:
                - 'title':        The song’s title
                - 'artist':       The song’s artist/album info
                - 'device_ip':    IP address of the device holding the song
                - 'file_path':    Path or URL to stream/download from the LAN
                - 'duration':     Song length in seconds
                - 'thumbnail':    Optional artwork URL or local path
        """
        # TODO: Query the server’s LAN-song-index database for `search_term`
        # TODO: Filter by `scope`, if necessary (e.g., exclude self)
        # TODO: Return a list of metadata dicts including device_ip & file_path
        raise NotImplementedError("LAN search is not yet implemented")


            