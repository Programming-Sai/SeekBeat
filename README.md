# SeekBeat

A lightweight, search-first music streaming and download backend powered by Django and yt-dlp. Quickly find, stream, or download music from YouTube with optional editing and playlist support. Designed for both web and desktop usage.

---

## 🔥 Project Overview

SeekBeat is an ambitious, multi-faceted music platform built in Django that aims to blend the best of online streaming (via YouTube) with truly local-first capabilities. At its core, SeekBeat lets users:

- **Discover** and **stream** music directly from YouTube links or search terms
- **Edit, download, and embed metadata** (ID3 tags) on-the-fly
- **Share and stream** music over a local area network (LAN) without relying on any cloud storage
- **Bookmark YouTube tracks** via a Chrome Extension, so you can save songs for later without copy-pasting

Under the hood, SeekBeat is designed as a series of independent Django “apps” (modules), each handling a specific slice of functionality. Whether you’re an end user looking for an all-in-one desktop-oriented music hub, or a frontend developer curious about integrating SeekBeat’s endpoints into a custom UI, this repository is built to be modular, extensible, and (eventually) cross-platform.

---

## 🚀 Key Features

1. **YouTube-Powered Streaming & Search**
   - Search by title, artist, lyrics snippet, or full YouTube URL
   - Fetch direct stream URLs and basic metadata (title, duration, thumbnail) via `yt-dlp`
   - Graceful fallback to YouTube Data API if configured
   - Trim, speed, and volume edits before streaming or downloading

2. **LAN-Based Device & File Sharing**
   - Create a LAN “host” session protected by a UUID-based access code (shared via QR code)
   - Join from any other device on the same network to browse or download songs directly
   - Register, reconnect, list, and disconnect devices; CRUD for song metadata and file uploads

3. **Chrome Extension Integration**
   - Browser extension that captures YouTube video metadata (“Save Song”) and pushes it to SeekBeat
   - CRUD API for bookmarks with UUID primary keys, auto-generated Swagger docs, and DRF Spectacular

4. **On-the-Fly Audio Editing & Metadata Injection**
   - Stream raw YouTube audio or produce on-the-fly MP3 with ID3 tags, cover art, and custom metadata
   - Support for trimming start/end times, adjusting speed and volume, and embedding tags via `mutagen`
   - Real-time streaming pipeline when metadata injection isn’t needed

5. **Modular, Pluggable Django Apps**
   - Each module (search, stream, LAN, Chrome Extension) is a self-contained Django app
   - Configurable via environment variables for “web” (cloud) vs “desktop” (local) modes
   - Designed for eventual feature branches: a production-ready web branch (no local file I/O) and a desktop branch bundled via PyInstaller

---

## 🏗️ Architecture & Module Breakdown

SeekBeat is organized into four main Django “apps” (plus supporting folders). This modular structure makes it straightforward to spin up only the pieces you need or build custom frontends against specific endpoints.

```
SeekBeat/
├─ chrome_extension/         # Django app for “Save Song” Chrome extension
├─ desktop_lan_connect/      # LAN hosting/joining, device management, file uploads
├─ search/                   # YouTube search (single & bulk) endpoints via yt-dlp / YouTube Data API
├─ stream/                   # YouTube streaming & editing (trim, speed, volume, ID3)
├─ ffmpeg/                   # Helper files for ffmpeg binaries (bundling for desktop)
├─ logs/                     # Default log directory (overridden per environment)
├─ seekbeat/                 # Core Django project settings, URLs, and middleware
└─ README.md                 # This project overview (you are here!)
```

Below is a high-level summary of each module—what it offers, what you can do with it, and why it matters:

---

### 1. **chrome_extension/**

A lightweight Django app that powers SeekBeat’s official Chrome Extension for “saving” YouTube video metadata without copy-pasting:

- **What it does**
  - CRUD endpoints under `/api/ext/` to create, list, retrieve, and delete “bookmarked” YouTube videos
  - Uses UUID primary keys for unguessable IDs
  - Auto-generated OpenAPI schema and Swagger UI via DRF & drf-spectacular

- **Key capabilities**
  - POST new video metadata (`title`, `duration`, `uploader`, `thumbnail`, `webpage_url`, `upload_date`)
  - GET a list of all captured videos or a single video by its UUID
  - DELETE individual bookmarks or all bookmarks at once

- **Ideal use case**
  - If you’re building a frontend (e.g., React app) or a Chrome Extension content script, you can integrate these endpoints to let users “Save” the current YouTube tab’s video info directly into SeekBeat’s database.

---

### 2. **desktop_lan_connect/**

A self-hosted, file-based Django API for peer-to-peer music sharing on your local network:

- **What it does**
  - Lets one device become the “host” by creating a session (UUID + QR code) under `/api/lan/`
  - Other devices provide the session’s access code to join the session
  - Once joined, clients can register themselves, upload MP3 files, CRUD song metadata, and download shared songs

- **Key capabilities**
  - **Session Management**: Create, check, and terminate LAN sessions (`/session-start/`, `/session-check/`, `/session-end/`)
  - **Device Lifecycle**: Connect, reconnect, list, and disconnect devices (`/device-connect/`, `/device-reconnect/`, `/device-disconnect/`, `/devices/`)
  - **Song Metadata & File Upload**:
    - List all songs for a device or delete them
    - Bulk add or single add metadata records
    - Upload MP3 files against a song UUID
    - Edit or delete a single song’s metadata or file

- **Why it matters**
  - You can run this app on a laptop/desktop, share its QR code—then any phone, tablet, or other computer on the same Wi-Fi can browse, stream, or download songs directly from the host, without any cloud involved.

---

### 3. **search/**

A standalone Django “search engine” app offering YouTube-based music search (single and bulk) via `yt-dlp` (with optional YouTube Data API keys):

- **What it does**
  - Provides two endpoints under `/api/search/`:
    1. **Single Search** (`GET /api/search/?query=<term or URL>`)
    2. **Bulk Search** (`GET /api/search/bulk/?queries=<comma-separated terms>`)

- **Key capabilities**
  - Query by song title, artist, lyrics snippet, or full YouTube link
  - Gracefully falls back from the YouTube Data API to `yt-dlp` scraping if API keys are missing or invalid
  - Rate limiting (25 requests/minute for single, 5 requests/minute for bulk, per IP)
  - Configurable via environment variables (max results, retries, concurrency, API keys)

- **Ideal use case**
  - Any frontend (web or mobile) can call these endpoints to quickly retrieve YouTube metadata—thumbnails, durations, uploader names—without pulling heavy video data. Great for building playlists, search UIs, or preview features.

---

### 4. **stream/**

A Django app that powers YouTube streaming, on-the-fly audio editing, and ID3 metadata embedding. It’s where heavy lifting happens via `yt-dlp`, `ffmpeg`, and `mutagen`:

- **What it does**
  - **GET /api/stream/{video_id}/** → Returns a JSON payload with a direct audio stream URL (no editing) and basic metadata
  - **POST /api/stream/{video_id}/** → Accepts an optional “edits” JSON body (trim, speed, volume, metadata), then streams back an edited MP3 file with embedded ID3 tags

- **Key capabilities**
  1. **`extract_stream_url(video_url)`**: Uses `yt-dlp` to fetch a direct audio URL and YouTube metadata (title, duration, thumbnail).
  2. **`stream_with_edits(input_src, edits)`**:
     - **Metadata branch** (desktop mode + metadata provided):
       - Downloads raw audio, applies trim/speed/volume via a single FFmpeg pass, converts to MP3, embeds ID3 tags & cover art via `mutagen`, streams the resulting file.

     - **Real-time branch** (no metadata):
       - Pipes the original stream through FFmpeg, applying filters on-the-fly, preserves existing ID3 tags, and streams chunks directly to the HTTP response.

- **Why it matters**
  - Instead of just sending a YouTube link to the client (which would leave actual streaming to the browser), SeekBeat’s streaming module lets you control bitrate, embed metadata, and even do quick snips—all without saving large files locally on the server. It’s ideal for lightweight, just-in-time streaming UIs.

---

## 🎨 Overall Workflow (For a New User)

1. **Install or fork the repo** and spin up the Django server (in “dev” mode, all modules are active).
2. **Search** for a song via `/api/search/` (see the Search App module).
3. **Stream** or **edit & download** via `/api/stream/` (see the Streaming module).
4. **Optionally**, if you run the LAN module on a local desktop:
   - Create a LAN session → scan QR on your phone’s browser → join the session → browse that desktop’s song library → stream or download directly.

5. **Optional**: Install the Chrome Extension to save YouTube video metadata into SeekBeat’s “bookmarks” (CRUD API under `/api/ext/`).

That “stacked” approach—Search → Stream/Edit → LAN share → Extension bookmark—illustrates SeekBeat’s versatility. You can use one or all of these modules, depending on your end goal.

---

## 🛠 Building the Executable (Using the Spec File)

To build the standalone `.exe` for the SeekBeat backend using the provided `SeekBeatServer.spec` file:

### 🔧 Requirements

- Python 3.12 installed
- `PyInstaller` installed globally:

```bash
pip install pyinstaller
```

- All project dependencies (install them via `requirements.txt` or `pip freeze`)

---

### ⚙️ How to Build

In the root of the project (same folder as `SeekBeatServer.spec`), run:

```bash
pyinstaller SeekBeatServer.spec
```

This will:

- Use the provided `.spec` file to control how the executable is bundled.
- Output a `SeekBeatServer.exe` file in the `dist/` folder.

---

## 🔐 API Key Configuration (New in v1.0.2)

To use the `.exe` version of SeekBeatServer with **YouTube Data API support**, you must provide your own API keys.

### 📁 File Structure Example

Place the following files in the **same directory**:

```ftt
./<your working folder>/*
        ├─ config/*
        |       └─ api.key
        └─ SeekBeatServer.exe #

```

> [!IMPORTANT]
> The folder name and sturcture must be exactly as is. the path to the api keys file should be exactly `config/api.key` and must be beside the .exe file. in dev mode, you can rename the [`example.api.key`](/config/example.api.key) to `api.key` and populate the skeleton in there, with just 2 youtube api keys or one, depending on which ever you want. however, without an api key for bulk search, bulk search would be disabled.

---

### ⚠️ Notes

- This `.spec` file is tailored for the **desktop version**, using local static files, templates, `.env`, and the local SQLite DB.
- Ensure you have a valid `.env` file before running the server.
- If you see errors like `Failed to load Python DLL`, try running from **outside** the `dist/` folder and make sure all required DLLs are accessible.

---

## 📂 What’s Next (Branches & Deployment)

- **`main` branch (“dev” mode)**: All modules active—ideal for local development and feature expansion.
- **`web` branch**: Strips out desktop-only file paths, disables LAN session creation, and configures only web-safe endpoints. Intended for PaaS deployment.
- **`desktop` branch**: Bundles ffmpeg and creates user-data directories for songs and QR codes. Enables full LAN hosting, local file I/O, and desktop packaging via PyInstaller or Electron.

_Read the README in each branch for environment-specific setup, deployment instructions, and contribution guidelines._

---

## 🤝 Contributing

SeekBeat is open for collaboration. If you’d like to help:

1. **Fork** the main repo and branch off of `main`.
2. Inform in an issue which feature or bug you’re working on.
3. Submit a **pull request**, referencing the issue and capturing any edge cases you addressed.
4. It will be reviewed and merged!

Whether you’re adding a new audio effect, optimizing the LAN discovery process, or building an Electron frontend, this codebase is structured to keep each concern isolated and testable.

---
