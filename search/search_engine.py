import random
import yt_dlp
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import requests
import os
import re

# from aiohttp import ClientSession


# https://www.youtube.com/shorts/5OU4sM47h6A?feature=share # TODO Youtube hacks



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
            # "noplaylist": True,              # Ignore playlists
            "quiet": True,                   # Suppress console output
            "skip_download": True,           # Do not download files
            # "extract_flat": "in_playlist",           # Get full metadata, not flat URLs
            # "default_search": "ytsearch",  # Allows plain terms as search
            # "source_address": "0.0.0.0",   # Avoid IPv6 resolution issues
            # "cachedir": False,               # Disable yt-dlp cache
            "no_warnings": True,             # Suppress warnings
            # "print_json": True,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.118 Safari/537.36"
        }

        # Use provided config, or fall back to defaults 
        self.config = config if config else self.SEARCH_YDL_OPTS
        # Initialize the yt-dlp extractor
        self.ydl = yt_dlp.YoutubeDL(self.config)
        # Default maximum number of results per query
        self.max_results = 10
        self.retries = 5
        self.max_concurrent_searches = 5
        self._sem = asyncio.Semaphore(self.max_concurrent_searches)
        self.BULK_API_KEY=os.getenv('BULK_SEARCH_YOUTUBE_API_KEY')


    def _execute_search(self, query: str):
        """
        Helper method to run the yt-dlp search synchronously.
        """
        return self.ydl.extract_info(query, download=False)

        


    async def regular_search(self, search_term: str, max_results: int = None, offset: int = None) -> list[dict] | dict:
        """
        Perform a single metadata search on YouTube.

        Args:
            search_term (str): The query string or URL.
            max_results (int, optional): Limit of results to return.
            offset (int, optional): Skip this many initial results.

        Returns:
            list[dict] or dict: A list of metadata dicts for matching videos,
                                or an error dict on failure.
        """
        if not search_term:
            return {"error": "No search term provided"}

        limit = max_results or self.max_results
        total_to_fetch = limit + (offset or 0)
        query = f"ytsearch{total_to_fetch}:{search_term}"

        for attempt in range(self.retries): 
            try:

                result = await asyncio.to_thread(self._execute_search, query)

                # with yt_dlp.YoutubeDL(self.config) as ydl:
                    # result = ydl.extract_info(query, download=False)

                # If it returns a playlist-like result
                if isinstance(result, dict) and result.get("_type") == "playlist":
                    entries = result.get("entries", [])
                    cleaned_entries = [
                        {
                            "title": e.get("title"),
                            "duration": e.get("duration"),
                            "uploader": e.get("uploader"),
                            "thumbnail": e.get("thumbnail"),
                            "webpage_url": e.get("webpage_url"),
                            'upload_date': e.get('upload_date'),
                            'largest_thumbnail': max(e.get('thumbnails', []), key=lambda t: t.get('height', 0) * t.get('width', 0)).get('url'),
                            'smallest_thumbnail': min(e.get('thumbnails', []), key=lambda t: t.get('filesize', float('inf'))).get('url'),
                        }
                        for e in entries[offset or 0:total_to_fetch]
                        if e and e.get("title") and e.get("webpage_url")
                    ]
                    # return cleaned_entries
                    return cleaned_entries

                # Single video fallback
                if isinstance(result, dict) and result.get("title") and result.get("webpage_url"):
                    return [{
                        "title": result.get("title"),
                        "duration": result.get("duration"),
                        "uploader": result.get("uploader"),
                        "thumbnail": result.get("thumbnail"),
                        "webpage_url": result.get("webpage_url"),
                        'upload_date': result.get('upload_date'),
                        'smallest_thumbnail': min(result.get('thumbnails', []), key=lambda t: t.get('filesize', float('inf'))).get('url'),
                    }]

                return {"error": "No usable results returned"}

            except Exception as e:
                if attempt == self.retries - 1:  # Last attempt
                    return {"error": f"An error occurred while searching for {search_term}: {str(e)}"}
            
                # Exponential backoff with some random jitter
                wait_time = min(2 ** attempt + random.uniform(0, 1), 10)  # Max delay of 10 seconds
                await asyncio.sleep(wait_time)


    async def _wrapped_search(self, term: str, max_results_per_term: int) -> dict:
        """
        Perform the search and return the result with the term.

        Args:
            term (str): The search term.
            max_results_per_term (int): Max results to return.

        Returns:
            dict: The result containing the term, results, and error info if any.
        """
        try:
            data = await self.regular_search_with_yt_api(term, max_results=10)
            # data = await self.regular_search(term, max_results_per_term)
            return {
                'search_term': term,
                'results': data,
                'count': len(data) if isinstance(data, list) else 0
            }
        except Exception as e:
            # In case of an error, return the error information
            return {
                'search_term': term,
                'error': str(e),
                'count': 0
            }




    async def bulk_search(self, search_terms: list[str], max_results_per_term: int =5) -> list[dict]:
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

        # Wrap each search term with its result in a task
        async def sem_wrapped(term):
            async with self._sem:
                print(f"Starting search for {term}")
                return await self._wrapped_search(term, max_results_per_term)

        tasks = [asyncio.create_task(sem_wrapped(term)) for term in search_terms]
        return await asyncio.gather(*tasks)
    

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


            




    # Function to parse duration (ISO 8601 format)
    def _parse_duration(self, duration_str):
        # The YouTube API returns the duration in ISO 8601 format, e.g., PT2M30S
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        # Return total duration in seconds
        return hours * 3600 + minutes * 60 + seconds

    # Main function to get and clean data
    async def regular_search_with_yt_api(self, search_term, api_key=None, max_results=50, page_token=None):
        api_key = api_key or self.BULK_API_KEY

        if not api_key:
            raise ValueError("Youtube API key Not Provided, or is invalid.")
        
        # Construct the API URL
        url = "https://www.googleapis.com/youtube/v3/search"
        
        params = {
            'part': 'snippet',
            'maxResults': max_results,
            'q': search_term,
            'key': api_key,
            'type': 'video',
            'pageToken': page_token,  # For pagination if available
        }

        # Make the request to YouTube API
        response = await asyncio.to_thread(requests.get, url, params)
        if response.status_code != 200:
            raise Exception(f"Error fetching data from YouTube API: {response.status_code}")
        
        data = response.json()
        
        cleaned_entries = []
        
        for e in data.get('items', []):
            entry = {
                "title": e.get("snippet", {}).get("title"),
                "duration": None,  # We will fetch the duration separately for each video
                "uploader": e.get("snippet", {}).get("channelTitle"),
                "thumbnail": e.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url"),
                "webpage_url": f"https://www.youtube.com/watch?v={e.get('id', {}).get('videoId')}",
                'upload_date': e.get("snippet", {}).get('publishedAt'),
                'largest_thumbnail': max(
                    e.get("snippet", {}).get('thumbnails', {}).values(),
                    key=lambda t: t.get('height', 0) * t.get('width', 0)
                ).get('url'),
                'smallest_thumbnail': min(
                    e.get("snippet", {}).get('thumbnails', {}).values(),
                    key=lambda t: t.get('filesize', float('inf'))
                ).get('url'),
            }

            # Fetch video details to get the duration
            video_id = e.get('id', {}).get('videoId')
            if video_id:
                duration_url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={api_key}"
                duration_response = await asyncio.to_thread(requests.get, duration_url)
                if duration_response.status_code == 200:
                    duration_data = duration_response.json()
                    video_duration = duration_data['items'][0].get('contentDetails', {}).get('duration')
                    entry["duration"] = self._parse_duration(video_duration)
            
            cleaned_entries.append(entry)

        return cleaned_entries
        # return cleaned_entries
