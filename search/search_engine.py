import json
import random
import yt_dlp
import asyncio
import requests
import os
import re
import unicodedata
from django.db.models import Q
from config import IS_DESKTOP
import logging
# from yt_dlp.cookies import extract_cookies_from_browser
# from yt_dlp.YoutubeDL import _YDLLogger



# from yt_dlp.utils import load_cookies_from_browser


from desktop_lan_connect.models import DeviceProfile, SongProfile
logger = logging.getLogger('seekbeat')



# from aiohttp import ClientSession


# https://www.youtube.com/shorts/5OU4sM47h6A?feature=share # TODO Youtube hacks


# def get_cookies():
#     with open(r"c:\\Users\\pc\\Desktop\\Projects\\SeekBeat\\cookies.json", "r") as f:
#         data = json.load(f)   
#         return data["cookies"]



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
        

        # try:
        #     cookies = extract_cookies_from_browser(
        #         browser_name="chrome",
        #         profile="Mensah",
        #         logger=_YDLLogger(),
        #         domain_name="youtube.com"
        #     )
        # except Exception as e:
        #     logger.error(f"Failed to load cookies from browser: {e}")
        #     cookies = None

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
            # "cookies": "C:\\Users\\pc\\desktop\\cookies.txt",
            # "cookies": cookies,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.118 Safari/537.36"
        }

        # Use provided config, or fall back to defaults 
        self.config = config if config else self.SEARCH_YDL_OPTS

        logger.debug("Initializing SearchEngine with config: %s", self.config)
        # Initialize the yt-dlp extractor
        self.ydl = yt_dlp.YoutubeDL(self.config)
        # Default maximum number of results per query
        self.max_results = 10
        self.retries = 5
        self.max_concurrent_searches = 2
        self._sem = asyncio.Semaphore(self.max_concurrent_searches)
        self.max_query_length = 500
        self.max_bulk_search = 5
        self.BULK_API_KEY= None
        self.NORMAL_API_KEY= None


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
        limit = max_results or self.max_results
        total_to_fetch = limit + (offset or 0)

        
        if search_term['type'] == 'invalid':
            return search_term['reason']
        elif search_term['type'] == 'youtube':
            search_term = search_term['query']
            query = f"{search_term}"
        elif search_term['type'] == 'search':
            search_term = search_term['query']
            query = f"ytsearch{total_to_fetch}:{search_term}"

        logger.info("yt-dlp search for query=%s", query)

      

        for attempt in range(self.retries): 
            if attempt > 0:
                print(f"Scrapper Retry: {attempt}/{self.retries}")
                logger.debug(f"Scrapper Retry: {attempt}/{self.retries} for search term: {query}")
            try:

                result = await asyncio.to_thread(self._execute_search, query)
                logger.debug("yt-dlp returned type=%s for query=%s", result.get('_type'), query)
                

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
                            'largest_thumbnail': max(e.get('thumbnails', []), key=lambda t: t.get('height', 0) * t.get('width', 0)).get('url') if e.get('thumbnails', []) else e.get('thumbnail'),
                            'smallest_thumbnail': min(e.get('thumbnails', []), key=lambda t: t.get('filesize', float('inf'))).get('url')  if e.get('thumbnails', []) else e.get('thumbnail'),
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
                        "smallest_thumbnail": min(result.get('thumbnails', []), key=lambda t: t.get("filesize", float("inf"))).get("url") if result.get('thumbnails', []) else result.get("thumbnail"),
                    }]

                return {"error": "No usable results returned"}

            except Exception as e:
                logger.exception("yt-dlp error on attempt %d for query=%s", attempt, query)
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

            data = await self.regular_search_with_yt_api(term, max_results=max_results_per_term, bulk=True)  
            return {   
                'search_term': term,
                'results': data,
                'count': len(data) if isinstance(data, list) else 0
            }
        except Exception as e:
            # In case of an error, return the error information
            logger.exception(f"Error fetching data for YouTube link {term['query']}: {e}")
            return {
                'search_term': term,
                'error': str(e),
                'count': 0
            }


    async def bulk_search(self, search_terms: list[str], max_results_per_term: int = 10) -> list[dict]:
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
                logging.debug(f"Starting search for {term}")
                return await self._wrapped_search(term, max_results_per_term)

        tasks = [asyncio.create_task(sem_wrapped(term)) for term in (search_terms if len(search_terms) <= self.max_bulk_search else search_terms[:self.max_bulk_search])]
        return await asyncio.gather(*tasks)
    



    def lan_search(self, search_term: str) -> list[dict]:
        """
        Searches all registered songs in the LAN.

        Args:
            search_term (str): Term to look up in title or artist.

        Returns:
            List[dict]: Song metadata results from active devices.
        """
        try:
            # Get all active devices
            active_device_ids = DeviceProfile.objects.filter(is_active=True).values_list("id", flat=True)

            # Query for matching songs from active devices
            matches = SongProfile.objects.filter(
                Q(device_id__in=active_device_ids),
                Q(title__icontains=search_term) | Q(artist__icontains=search_term)
            ).select_related("device")

            # Build the result list
            results = []
            for song in matches:
                device = song.device
                if device and device.ip_address:  # Ensure IP exists
                    results.append({
                        "title": song.title,
                        "artist": song.artist or "Unknown",
                        "device_ip": device.ip_address,
                        "device_id": str(device.device_id),
                        "song_id": str(song.song_id),
                        "duration": song.duration_seconds
                    })
            return results
        except Exception as e:
            print(str(Exception))



     
    def _parse_duration(self, duration_str):
        # The YouTube API returns the duration in ISO 8601 format, e.g., PT2M30S
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        # Return total duration in seconds
        return hours * 3600 + minutes * 60 + seconds

    
    async def regular_search_with_yt_api(self, search_term, api_key=None, max_results=50, page_token=None, bulk=False):
        logger.info("YT-API search for term=%s (bulk=%s)", search_term, bulk)   

        query = search_term
        if search_term['type'] == 'invalid':
            return search_term['reason']
        elif search_term['type'] == 'youtube':
            return await self.regular_search(search_term)
        elif search_term['type'] == 'search':
            search_term = search_term['query']

        api_key = api_key or self.NORMAL_API_KEY

        


        try:
            if not api_key:
                logger.warning("No API key provided; using yt-dlp fallback.")
                raise ValueError("Youtube API key Not Provided, or is invalid.")

            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'maxResults': max_results,
                'q': search_term,
                'key': api_key,
                'type': 'video',
                'pageToken': page_token,
            }

            response = await self._retry_request(url, params, search_term, retries=self.retries)
            # raise Exception("Simulated Exception to test yt-dlp Fall back") # Fall back caller for testing.
            data = response.json()
            logger.debug("YT-API returned %d items for term=%s", len(data.get('items', [])), search_term)
        except Exception as e:
            logger.exception("Failed parsing JSON for term=%s", search_term)
            print(f"Youtube API failed after retries: {e}")
            if bulk and not IS_DESKTOP:
                logger.warning("Bulk fallback: aborting bulk for term=%s", search_term) 
                raise Exception("Bulk Search API is currently unavailable. Try again later.")
            logger.info("Falling back to yt-dlp for term=%s", search_term)
            return await self.regular_search(query)  # Fallback here

        video_ids = [e.get('id', {}).get('videoId') for e in data.get('items', []) if e.get('id', {}).get('videoId')]

        # Fetch all durations in parallel
        durations = await self._fetch_durations_parallel(video_ids, api_key)

        cleaned_entries = []

        for e in data.get('items', []):
            video_id = e.get('id', {}).get('videoId')
            entry = {
                "title": e.get("snippet", {}).get("title"),
                "duration": durations.get(video_id),  # fast lookup
                "uploader": e.get("snippet", {}).get("channelTitle"),
                "thumbnail": e.get("snippet", {}).get("thumbnails", {}).get("high", {}).get("url"),
                "webpage_url": f"https://www.youtube.com/watch?v={video_id}",
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
            cleaned_entries.append(entry)

        return cleaned_entries




    async def _retry_request(self, url, params, search_term, retries=3):
        for attempt in range(retries):
            try:
                if attempt > 0:
                    print(f"Api Retry for '{search_term}': {attempt}/{self.retries}")
                    logger.debug("Retry %d for term=%s", attempt, search_term) 


                # Simulate API failure for testing
                # raise Exception("Simulated API failure for testing.")

                response = await asyncio.to_thread(requests.get, url, params=params)
            
                # raise Exception("Simulated API failure for testing.")
            
                if response.status_code == 200:
                    logger.debug("Request success for term=%s", search_term)  # 🔹 LOG HERE
                    return response
                else:
                    logger.warning("Non-200 (%s) for term=%s: %s", response.status_code, search_term, response.text)  # 🔹 LOG HERE

                    error_data = response.json()
                    reason = error_data.get('error', {}).get('errors', [{}])[0].get('reason', '')

                    if response.status_code == 403 and reason in ['quotaExceeded', 'userRateLimitExceeded']:
                        raise Exception("Quota exceeded.")
                    if response.status_code not in {500, 503}:
                        raise Exception(f"Unrecoverable error: {response.status_code}")

            except Exception as e:
                print(f"Request attempt {attempt+1} failed with error: {e}")
                logger.exception(f"Request attempt {attempt+1} failed with error: {e}")

            await asyncio.sleep(1)  # small delay before retry

        raise Exception(f"Failed after {retries} retries.")



    async def _fetch_durations_parallel(self, video_ids, api_key):
        async def fetch_duration(video_id):
            url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={api_key}"
            try:
                resp = await asyncio.to_thread(requests.get, url)
                if resp.status_code == 200:
                    duration_data = resp.json()
                    raw_duration = duration_data['items'][0].get('contentDetails', {}).get('duration')
                    return video_id, self._parse_duration(raw_duration)
            except Exception:
                pass
            return video_id, None

        tasks = [fetch_duration(vid) for vid in video_ids]
        results = await asyncio.gather(*tasks)
        return dict(results)



# Sanitzation and input validation



    def _is_youtube_link(self, query: str) -> bool:
        """
        Check if the query is a valid YouTube link.
        """
        return bool(re.search(r'https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})', query))

    def _clean_query(self, query: str) -> str:
        """
        Clean and normalize the input query.
        - Trims whitespace
        - Normalizes unicode characters
        - Collapses repeated spaces
        """
        # Normalize unicode (e.g. converting accented characters to their basic form)
        query = unicodedata.normalize('NFKC', query)

        # Remove leading and trailing whitespace
        query = query.strip()

        # Collapse multiple spaces to a single one
        query = re.sub(r'\s+', ' ', query)

        return query

    def _validate_query(self, query: str) -> bool:
        """
        Validate the input query for basic safety and length.
        - Ensure the query isn't empty after cleaning.
        - Reject queries that are too long or too short.
        """
        # Ensure query isn't empty or just whitespace
        if not query:
            return {'type': 'invalid', 'query': query, 'reason':'This is an empty query. please place some search term or youtube link.'}, False
        
        # Optional: Reject queries that are too long or too short
        if len(query) > self.max_query_length:  # Arbitrary max length
            return {'type': 'invalid', 'query': query, 'reason': 'This query is too long. Please shorten it.'}, False
        
        return {'type': 'valid', 'query': query}, True

    def clean_and_classify_query(self, query: str):
        """
        Main function that detects if the query is a YouTube link or a search term.
        - Cleans the query
        - Detects if it's a valid YouTube link or a search term
        - Returns structured result: {'type': 'youtube'/'search', 'query': cleaned query}
        """
        # Clean and validate the query
        query = self._clean_query(query)
        invalidity_reason, validity = self._validate_query(query)
        if not validity:
            return invalidity_reason

        # Check if it's a YouTube link
        if self._is_youtube_link(query):
            return {'type': 'youtube', 'query': query}
        
        # Otherwise treat it as a search term
        return {'type': 'search', 'query': query}
