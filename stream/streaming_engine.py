
# streaming/services/engine.py

import yt_dlp

class StreamingEngine:
    def __init__(self):
        self.ytdlp_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "nocheckcertificate": True,
            "noplaylist": True,
            "skip_download": True,
        }

    def extract_stream_url(self, video_url: str) -> dict:
        try:
            with yt_dlp.YoutubeDL(self.ytdlp_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return {
                    "stream_url": info["url"],
                    "title": info.get("title"),
                    "duration": info.get("duration"),
                    "thumbnail": info.get("thumbnail"),
                    "source": "youtube"
                }
        except Exception as e:
            raise RuntimeError(f"Failed to extract stream URL: {str(e)}")
