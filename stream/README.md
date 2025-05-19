# SeekBeat Streaming Module

A Django-powered back‑end for streaming YouTube audio with on‑the‑fly editing (trim, speed, volume) and ID3 metadata embedding. This API can be used to:

- **Fetch** a direct stream URL & basic metadata (title, duration, thumbnail)
- **Stream** edited audio (MP3) via HTTP, applying:

  - Trimming (start/end timestamps)
  - Speed adjustment
  - Volume adjustment
  - Metadata injection (title, artist, album, date, genre, URL, cover art)

---

## 📦 Installation

1. **Clone** your project and install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. **Ensure** you have an `ffmpeg` binary installed or let `imageio-ffmpeg` download one for you—our module copies it into `ffmpeg/ffmpeg.exe` by default.
3. **Add** the `stream` app to your `INSTALLED_APPS` and include its URLs:

   ```python
   # settings.py
   INSTALLED_APPS += [
       'rest_framework',
       'drf_spectacular',
       'django_ratelimit',
       'stream',
   ]

   # urls.py
   from django.urls import path, include

   urlpatterns = [
       # ...
       path('api/stream/', include('stream.urls')),
   ]
   ```

---

## 🔗 API Endpoints

### 1. Get Raw Stream URL & Metadata

```
GET /api/stream/{video_id}/
```

- **Path Parameter**

  - `video_id`: the YouTube video ID (e.g. `dQw4w9WgXcQ`) or full URL

- **Response (200 JSON)**

  ```json
  {
    "stream_url": "https://...googlevideo.com/...",
    "title": "Rick Astley – Never Gonna Give You Up",
    "duration": 212,
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "source": "youtube"
  }
  ```

- **Errors**

  - `400`: missing/invalid `video_id`
  - `500`: extraction failure

### 2. Stream Edited Audio (MP3)

```
POST /api/stream/{video_id}/
Content-Type: application/json
```

- **Body**

  ```json
  {
    "edits": {
      "speed": 1.25,
      "trim": {
        "start_time": 10,
        "end_time": 120
      },
      "volume": 0.5,
      "metadata": {
        "title": "The High Seas' Anthem",
        "artist": "Pirate Sea Shanty - Topic",
        "album": "Sea Shanties Vol.1",
        "date": "2025-05-19",
        "genre": "Folk",
        "url": "https://youtu.be/V_N1MavsGJE",
        "thumbnail": "https://i.ytimg.com/vi_webp/V_N1MavsGJE/maxresdefault.webp"
      }
    }
  }
  ```

  - **All fields are optional**—omit `edits` or pass `{}` for a plain MP3 download.
  - **`speed`**: playback rate (`0.5`–`2.0`)
  - **`trim.start_time`** & **`trim.end_time`**: seconds into the track
  - **`volume`**: gain multiplier (`0.5`–`5.0`)
  - **`metadata`**: ID3 tags to embed; includes cover art URL

- **Response (200, audio/mpeg)**

  - Streams an MP3 file; the `Content-Disposition` header sets the filename to `{title}.mp3`.
  - Example header:

    ```
    Content-Disposition: attachment; filename="The High Seas' Anthem.mp3"
    ```

- **Errors**

  - `400`: malformed JSON
  - `500`: FFmpeg or metadata injection failure

---

## 🛠️ Under the Hood

- **`StreamingEngine.extract_stream_url(video_url)`**

  - Uses `yt-dlp` to fetch the direct audio URL & YouTube metadata.

- **`StreamingEngine.stream_with_edits(input_src, edits)`**

  - **Metadata branch** (desktop mode + `metadata` provided):

    1. Downloads raw audio & applies any trim/speed/volume via a single FFmpeg pass.
    2. Converts to MP3, embeds ID3 tags & cover art via `mutagen`.
    3. Streams the resulting file, then cleans up temp files.

  - **Real‑time branch** (no metadata):

    1. Pipes the original stream through FFmpeg, applying trim/speed/volume filters.
    2. Preserves existing ID3 tags.
    3. Streams chunks to the HTTP response and terminates cleanly.

- **Cleanup**

  - Temporary files are deleted asynchronously via daemon threads.

---

## 🚀 Example Client Use

### Fetching stream URL (JavaScript + fetch)

```js
fetch("/api/stream/dQw4w9WgXcQ/")
  .then((res) => res.json())
  .then((info) => {
    console.log(info.title, info.stream_url);
    // e.g. set audio.src = info.stream_url
  });
```

### Downloading edited MP3

```js
const edits = {
  speed: 1.25,
  trim: { start_time: 10, end_time: 120 },
  volume: 0.5,
  metadata: { title: "My Song", artist: "Me", url: "https://youtu.be/..." },
};

fetch("/api/stream/dQw4w9WgXcQ/", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ edits }),
})
  .then((res) => res.blob())
  .then((blob) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "My Song.mp3";
    a.click();
  });
```

---

## 📝 Testing & Docs

- **Rate‑limit**: 30 requests per minute per IP.
- **OpenAPI**:

  - Schema generated via **drf-spectacular**
  - Examples for both GET & POST appear in Swagger/Redoc.

- **Local Test Redirect** (no DRF):

  ```
  GET /api/stream/test/?id=dQw4w9WgXcQ
  ```

  Redirects to the raw `stream_url`.

---
