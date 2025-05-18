import yt_dlp
import subprocess
import imageio_ffmpeg
import os
import shutil


class StreamingEngine:
    def __init__(self):
        self.ytdlp_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "nocheckcertificate": True,
            "noplaylist": True,
            "skip_download": True,
        }
        custom_dir = os.path.abspath(r"c:\Users\pc\Desktop\Projects\SeekBeat\ffmpeg")
        custom_path = os.path.join(custom_dir, "ffmpeg.exe")


       # Download it if not already present
        if not os.path.exists(custom_path):
            print("Downloading FFmpeg via imageio-ffmpeg...")
            default_path = imageio_ffmpeg.get_ffmpeg_exe()
            os.makedirs(custom_dir, exist_ok=True)
            shutil.copy2(default_path, custom_path)

        # Set env var so other libraries can use it
        os.environ["IMAGEIO_FFMPEG_EXE"] = custom_path
        self.ffmpeg_path = custom_path
        print("Using FFmpeg at:", self.ffmpeg_path)

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

    def stream_with_edits(self, video_url, edits: dict):
        info = self.extract_stream_url(video_url)
        input_url = info["stream_url"]

        # Start building ffmpeg command
        cmd = [
            self.ffmpeg_path,
            "-nostdin",
            "-i", input_url,
            "-vn",  # no video
            "-f", "mp3",  # output format
            "-acodec", "libmp3lame",
            "-loglevel", "quiet"
        ]

        # Apply trim
        if "start_time" in edits:
            cmd.insert(1, "-ss")
            cmd.insert(2, str(edits["start_time"]))
        if "end_time" in edits:
            cmd += ["-to", str(edits["end_time"])]

        # Build filter chain
        filters = []

        if "volume" in edits:
            filters.append(f"volume={edits['volume']}")
        if "speed" in edits:
            # Speed affects tempo and pitch unless compensated
            filters.append(f"atempo={edits['speed']}")

        if filters:
            cmd += ["-af", ",".join(filters)]

        cmd += ["-"]
        # print(cmd)

        # Pipe output to response
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            return process.stdout
        except Exception as e:
            raise RuntimeError(f"Failed to stream with edits: {str(e)}")
