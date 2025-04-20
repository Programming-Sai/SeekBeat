import yt_dlp
from concurrent.futures import ThreadPoolExecutor, as_completed



class SearchEngine:
    def __init__(self, config=None):
        self.SEARCH_YDL_OPTS = {
            "format": "bestaudio/best",     # get best quality audio
            "noplaylist": True,             # don't pull entire playlists
            "quiet": True,                  # suppress logs
            "skip_download": True,          # don't actually download
            "extract_flat": "in_playlist", # allows faster extraction of metadata only (flattened results)
            "default_search": "ytsearch",  # makes it easy to just search with a term
            "source_address": "0.0.0.0",    # avoids IP-related issues (optional)
        }

        # Apply global config or default to SEARCH_YDL_OPTS
        self.config = config if config else self.SEARCH_YDL_OPTS
        self.ydl = yt_dlp.YoutubeDL(self.config)
        self.max_results = 10

    
    def regular_search(self, search_term, max_results=None, offset=None):
        try:
            # Perform the search query using yt-dlp
            limit = max_results or self.max_results
            total_to_fetch = limit + (offset or 0)

            result = self.ydl.extract_info(f"ytsearch{total_to_fetch}:{search_term}", download=False)
            if result.get("_type") == "playlist":
                return result["entries"]
            return [result]  # fallback if it’s a single video
        except Exception as e:
            return {"error": f"An error occurred: {str(e)}"}


    def bulk_search(self, search_terms):
        results = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.regular_search, term) for term in search_terms]
            for future in as_completed(futures):
                results.append(future.result())

        return results
            
        