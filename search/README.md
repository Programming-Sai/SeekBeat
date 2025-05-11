# Search App for SeekBeat 🎶🔍

A standalone Django app providing YouTube-based music search (single and bulk) powered by `yt-dlp` with graceful fallback to the YouTube Data API. Perfect for integrating into music players, playlist generators, or any service requiring fast metadata-only lookups.

---

## 🚀 Features

- **Single Search**
  Query by song title, artist name, lyrics snippet, or direct YouTube link
- **Bulk Search**
  Up to **10** comma-separated queries in one request (titles, artists, lyrics, or links)
- **Graceful Fallback**
  Tries YouTube Data API first (if API key provided), falls back to `yt-dlp` scraping
- **Rate-Limiting**
  Protects endpoints:

  - Single: 25 requests/minute per IP
  - Bulk: 5 requests/minute per IP

- **Configurable**
  Adjust max results, retries, concurrency, and API keys via environment

---

## 📦 Installation

Add the **search** app to your Django project:

1. **Clone** or copy this folder into your project.
2. **Install** dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. **Enable** in `settings.py`:

   ```python
   INSTALLED_APPS += [
     'search',
     'drf_spectacular',
   ]

   REST_FRAMEWORK = {
     'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
   }
   ```

4. **Include** URLs in your project’s `urls.py`:

   ```python
   from django.urls import path, include
   from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

   urlpatterns = [
     # … your other routes …
     path('api/search/', include('search.urls')),
     path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
     path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
   ]
   ```

---

## ⚙️ Configuration

Set these environment variables (optional; default is “scraper only” mode):

| Variable                        | Description                              |
| ------------------------------- | ---------------------------------------- |
| `NORMAL_SEARCH_YOUTUBE_API_KEY` | YouTube Data API key for single searches |
| `BULK_SEARCH_YOUTUBE_API_KEY`   | YouTube Data API key for bulk searches   |

_If keys are missing or invalid, the app silently falls back to `yt-dlp`._

---

## 📖 API Reference

All routes return JSON and are rate-limited by client IP.

### 1. Single Music Search

```
GET /api/search/?query=<SEARCH_TERM_OR_YT_LINK>
```

- **Parameters**

  - `query` (string, required):
      • Song title (e.g. `Hey Jude`)
      • Artist (e.g. `The Beatles`)
      • Lyrics snippet (e.g. `Here comes the sun`)
      • YouTube URL (e.g. `https://youtu.be/3tmd-ClpJxA`)

- **Responses**

  - `200 OK`

    ```json
    [
      {
        "title": "...",
        "duration": 215,
        "uploader": "...",
        "thumbnail": "...",
        "webpage_url": "...",
        "upload_date": "...",
        "largest_thumbnail": "...",
        "smallest_thumbnail": "..."
      },
      …
    ]
    ```

  - `400 Bad Request` – Missing/invalid `query`
  - `429 Too Many Requests` – >25 requests/minute
  - `500 Internal Server Error` – Unexpected error

#### cURL Example

```bash
curl "http://localhost:8000/api/search/?query=Imagine%20Dragons%20Believer"
```

---

### 2. Bulk Music Search

```
GET /api/search/bulk/?queries=<comma_separated_TERMS>
```

- **Parameters**

  - `queries` (string, required): Up to 10 comma-separated terms (titles, artists, lyrics, or links).
  - Extra terms beyond the first 10 are **ignored**.

- **Responses**

  - `200 OK`

    ```json
    [
      {
        "search_term": { "type": "search", "query": "Adele Hello" },
        "results": [
          /* … up to 10 items … */
        ],
        "count": 1
      },
      {
        "search_term": { "type": "youtube", "query": "https://youtu.be/XYZ" },
        "results": [
          /* … */
        ],
        "count": 1
      }
    ]
    ```

  - `400 Bad Request` – No valid terms provided
  - `429 Too Many Requests` – >5 requests/minute
  - `500 Internal Server Error`

#### cURL Example

```bash
curl "http://localhost:8000/api/search/bulk/?queries=Adele%20Hello,Bohemian%20Rhapsody,https://youtu.be/3tmd-ClpJxA"
```

---

## 🧪 Testing

1. **Unit tests** for `SearchEngine` in `search/tests/test_search_engine.py`.
2. **Integration tests** for views in `search/tests/test_views.py`.

Run them with:

```bash
 python -m unittest -f search.tests.test_search_engine

AND

 python manage.py test search.tests.test_views
```

---

## 🤝 Contributing

1. Fork & branch
2. Add tests for any new logic
3. Update docs (`README.md` & API examples)
4. Open a PR and we’ll review!
