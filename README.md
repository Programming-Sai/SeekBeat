# SeekBeat (Web)

A lightweight music search tool powered by Django and the YouTube Data API. This web demo lets you search for songs or artists on YouTube—but does not support streaming, downloading, or editing. For full functionality, see the desktop version.

---

## 🌐 Live Demo

Try it out at: [https://seekbeat.onrender.com](https://seekbeat.onrender.com)

> [!TIP]
> Simply enter a song title, artist name, direct link, or lyrics snippet into the query parameter and hit Enter to see results. at `api/search?query=`

---

## 🔍 Core Features (Web)

- **YouTube Search** via the YouTube Data API v3  
  • Returns title, duration, uploader, thumbnail, and video ID for matching results.  
  • Rate-limited by YouTube API quotas.

---

## ⚠️ Known Limitations (Web)

- **No Streaming or Metadata Enrichment**  
  yt-dlp fallback fails on cloud hosts due to bot detection (“Sign in to confirm you’re not a bot”), missing FFmpeg, and lack of filesystem writes.

- **No Audio/Video Download**  
  YouTube Data API does not provide direct media URLs. Downloading is not supported in this demo.

- **No yt-dlp Support on Web**  
  Attempting to extract stream URLs fails with CAPTCHA/login requirements and Render’s IP blacklisting.

- **YouTube Data API Quotas Can Be Exhausted**  
  Once the API key’s daily quota is reached, search requests will return errors or no results.

- **No User Login or Saved History**  
  All searches are anonymous and stateless. There is no account system, playlist, or in the web demo.

---

## ⚙️ Deployment Notes

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Programming-Sai/SeekBeat.git
   cd SeekBeat

   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Create and Configure `.env`**
   Copy the example and fill in your YouTube API key:

   ```bash
   cp .env.example .env
   ```

   Set:

   ```env
   SEEKBEAT_ENV=web
   YOUTUBE_API_KEY=your_youtube_data_api_key_here
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Static Files (if needed)**

   - Ensure `STATIC_URL = '/static/'` and `STATICFILES_DIRS = [BASE_DIR / "static"]` in `settings.py`.
   - Django’s `collectstatic` is run automatically in Render builds.

5. **Run Locally**

   ```bash
   python manage.py runserver
   ```

   Visit [http://127.0.0.1:8000](http://127.0.0.1:8000) and test the search.

6. **Render Deployment (example)**

   - Push the `web` branch to GitHub.

   - On Render.com, create a new Web Service:

     - **Branch:** `web`
     - **Build Command:**

       ```bash
       pip install -r requirements.txt && python manage.py collectstatic --noinput
       ```

     - **Start Command:**

       ```bash
       gunicorn seekbeat.wsgi --bind 0.0.0.0:$PORT
       ```

     - **Environment Variables:**
       • `DJANGO_SECRET_KEY` (set to a secure key)
       • `DJANGO_ALLOWED_HOSTS=seekbeat.onrender.com`
       • `BULK_SEARCH_YOUTUBE_API_KEY=your_youtube_data_api_key_here`
       • `NORMAL_SEARCH_YOUTUBE_API_KEY=your_youtube_data_api_key_here`

   - Make sure static files are served (Whitenoise is enabled by default in `settings.py`).

---

## 📄 `.env.example`

```env
# Set environment mode
BULK_SEARCH_YOUTUBE_API_KEY=

NORMAL_SEARCH_YOUTUBE_API_KEY=

SEEKBEAT_ENV=web

DJANGO_SECRET_KEY=

DJANGO_ALLOWED_HOSTS=



```

---

## 💡 Future Improvements

- **Cookie Support for yt-dlp** (Experimental)
  Allow users to upload their own YouTube cookies to attempt bypassing bot checks—though server IP may still be blocked.

- **Enhanced API Usage**
  Better error handling when API quotas are exhausted, with informative messages or fallback suggestions.

- **Desktop-First Optimization**
  Shift core download/edit/stream features into a standalone desktop application (Electron, Tauri, or native).

- **PWA for Offline Preview Mode**
  Allow caching of search results or thumbnails for occasional offline browsing.

---

## 📚 Documentation

- Full API documentation is available at `/api/docs/` (Swagger UI).
- For desktop installation, LAN streaming, and advanced features, refer to the **desktop branch** README.

---

## 🤝 Contributing

1. **Fork** this repository and create a branch off `web`.
2. Make your changes and run tests (if applicable).
3. Submit a **Pull Request** with a clear description of your changes.
4. We’ll review and merge as appropriate.

---
