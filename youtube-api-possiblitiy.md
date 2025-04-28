Perfect. I’ll put together a clean Python example showing how to use the YouTube Data API to search videos and fetch these exact fields:

- title
- duration
- uploader
- thumbnail
- webpage_url
- upload_date
- smallest_thumbnail

I'll also show how to format it similarly to what you are already returning, so it can easily replace your yt-dlp search.
I'll get this ready for you shortly!

# YouTube Data API v3: Async Python Search Example

To search YouTube videos by keyword, you use the **Search: list** endpoint of the YouTube Data API. First, enable **YouTube Data API v3** in the [Google Cloud Console](https://console.cloud.google.com) and create an **API key** (API & Services → Library → _YouTube Data API v3_ → Enable; then Credentials → Create API key) ([Python Quickstart  |  YouTube Data API  |  Google for Developers](https://developers.google.com/youtube/v3/quickstart/python#:~:text=1,is%20enabled%20for%20your%20project)). This key will authenticate your requests.

Key points for efficient use:

- **Search endpoint:** Use `search/list` with `part=snippet`, `q=<keywords>`, `type=video`, etc. For example, setting `type=video` restricts results to videos ([Implementation: Search requests  |  YouTube Data API  |  Google for Developers](https://developers.google.com/youtube/v3/guides/implementation/search#:~:text=This%20example%20calls%20the%20,parameters)).
- **Video details:** The search results give you video IDs. Then call `videos/list` with `part=snippet,contentDetails` (and `id=<comma-separated IDs>`) to fetch **duration** and full snippet data ([Using YouTube Data API v3 with Python — Search Videos by the keyword and get the video details | by Maurya Allimuthu | Medium](https://catchmaurya.medium.com/using-youtube-data-api-v3-with-python-search-videos-by-the-keyword-and-get-the-video-details-8062fe99ca22#:~:text=You%20need%20to%20use%20the,the%20duration%20of%20the%20video)).
- **Fields parameter:** Use the optional `fields` query parameter to return only needed sub-fields. For instance, setting `fields=items(id,snippet(title,channelTitle,publishedAt,thumbnails(default/url,high/url)),contentDetails/duration)` ensures each item includes only the specified JSON keys ([YouTube Data API Overview  |  Google for Developers](https://developers.google.com/youtube/v3/getting-started#:~:text=URL%3A%20https%3A%2F%2Fwww)). This reduces payload.

Below is a clean **async Python** example (using [`httpx`](https://www.python-httpx.org/)) that performs a search, fetches details, and formats the output similarly to yt-dlp’s JSON. It retrieves each video’s title, duration, channel title (uploader), upload date, thumbnail URLs, and URL.

```python
import httpx
import re
from datetime import datetime

async def search_youtube_videos(query: str, api_key: str, max_results: int = 5):
    # 1. Search: get video IDs and basic snippet info
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "key": api_key,
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        # Only request needed snippet fields: title, channelTitle, publishedAt, thumbnails URLs
        "fields": "items(id/videoId,snippet(title,channelTitle,publishedAt,thumbnails(default/url,high/url)))"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(search_url, params=search_params)
        data = resp.json()
    video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
    if not video_ids:
        return []

    # 2. Videos: get duration and any additional snippet info
    videos_url = "https://www.googleapis.com/youtube/v3/videos"
    videos_params = {
        "key": api_key,
        "part": "snippet,contentDetails",
        "id": ",".join(video_ids),
        # Only fetch the snippet fields we need plus duration
        "fields": "items(id,snippet(title,channelTitle,publishedAt,thumbnails(default/url,high/url)),contentDetails/duration)"
    }
    async with httpx.AsyncClient() as client:
        resp2 = await client.get(videos_url, params=videos_params)
        videos_data = resp2.json()

    results = []
    for item in videos_data.get("items", []):
        video_id = item["id"]
        snippet = item["snippet"]
        # Extract fields
        title = snippet.get("title")
        uploader = snippet.get("channelTitle")
        published_at = snippet.get("publishedAt")  # e.g. "2022-03-27T11:59:34Z"
        # Convert to YYYYMMDD format for consistency with yt-dlp's upload_date
        upload_date = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y%m%d")
        # Parse ISO 8601 duration (e.g. "PT1H2M3S") to seconds
        iso_duration = item["contentDetails"]["duration"]
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso_duration)
        hours = int(match.group(1)) if match and match.group(1) else 0
        minutes = int(match.group(2)) if match and match.group(2) else 0
        seconds = int(match.group(3)) if match and match.group(3) else 0
        duration = hours*3600 + minutes*60 + seconds

        # Select smallest and largest thumbnail URLs if available
        thumbs = snippet.get("thumbnails", {})
        thumb_small = thumbs.get("default", {}).get("url")
        thumb_large = thumbs.get("maxres", {}).get("url") or thumbs.get("high", {}).get("url")

        results.append({
            "title": title,
            "uploader": uploader,
            "upload_date": upload_date,
            "duration": duration,
            "thumbnails": {"small": thumb_small, "large": thumb_large},
            "webpage_url": f"https://www.youtube.com/watch?v={video_id}"
        })
    return results
```

**Explanation:** This code does the following:

- It calls the **Search endpoint** (`search/list`) with `part=snippet`, `type=video` and your query. We use `fields=items(id/videoId,snippet(title,channelTitle,publishedAt,thumbnails(default/url,high/url)))` so that each search result only includes the video ID and the snippet subfields we need (title, channel title, published date, and thumbnail URLs) ([YouTube Data API Overview  |  Google for Developers](https://developers.google.com/youtube/v3/getting-started#:~:text=URL%3A%20https%3A%2F%2Fwww)).
- From the search results, it collects all `videoId`s.
- It then calls **Videos endpoint** (`videos/list`) with `part=snippet,contentDetails` and those IDs. Again, it specifies fields to get each video’s `snippet` (title, channelTitle, publishedAt, thumbnails) and `contentDetails/duration`. This call returns each video’s metadata, including ISO-8601 duration ([Using YouTube Data API v3 with Python — Search Videos by the keyword and get the video details | by Maurya Allimuthu | Medium](https://catchmaurya.medium.com/using-youtube-data-api-v3-with-python-search-videos-by-the-keyword-and-get-the-video-details-8062fe99ca22#:~:text=You%20need%20to%20use%20the,the%20duration%20of%20the%20video)).
- The code parses the ISO 8601 `duration` into seconds, formats the `publishedAt` timestamp into `YYYYMMDD` as **upload_date**, and picks the smallest (`default`) and largest (`maxres` or fallback `high`) thumbnail URL. It constructs the standard YouTube URL `https://www.youtube.com/watch?v=VIDEO_ID` for each video.
- Finally, it returns a list of dictionaries in a structure similar to yt-dlp’s JSON output, with keys: `title`, `uploader`, `upload_date`, `duration` (int), `thumbnails` (with `small` and `large` URLs), and `webpage_url`.

**Usage Notes:** Run this in an `async` context (e.g. an async Django view). You need to install the `httpx` library (`pip install httpx`). Replace `api_key` with your own key. Adjust `max_results` or loop with `pageToken` if you need more results. By using the `fields` parameter, the code minimizes fetched data (only needed fields) ([YouTube Data API Overview  |  Google for Developers](https://developers.google.com/youtube/v3/getting-started#:~:text=URL%3A%20https%3A%2F%2Fwww)), which makes the search efficient and fast.

**References:** This approach follows the YouTube Data API documentation for **Search** and **Videos** endpoints ([Implementation: Search requests  |  YouTube Data API  |  Google for Developers](https://developers.google.com/youtube/v3/guides/implementation/search#:~:text=This%20example%20calls%20the%20,parameters)) ([Using YouTube Data API v3 with Python — Search Videos by the keyword and get the video details | by Maurya Allimuthu | Medium](https://catchmaurya.medium.com/using-youtube-data-api-v3-with-python-search-videos-by-the-keyword-and-get-the-video-details-8062fe99ca22#:~:text=You%20need%20to%20use%20the,the%20duration%20of%20the%20video)). The `fields` parameter usage is demonstrated in Google’s API examples ([YouTube Data API Overview  |  Google for Developers](https://developers.google.com/youtube/v3/getting-started#:~:text=URL%3A%20https%3A%2F%2Fwww)). The API key setup steps are as described in Google’s quickstart guide ([Python Quickstart  |  YouTube Data API  |  Google for Developers](https://developers.google.com/youtube/v3/quickstart/python#:~:text=1,is%20enabled%20for%20your%20project)).
