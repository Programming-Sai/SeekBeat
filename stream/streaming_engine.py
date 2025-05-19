import yt_dlp
import subprocess
import imageio_ffmpeg
import os
import shutil
import logging

logger = logging.getLogger('seekbeat')
handler = logging.getLogger('seekbeat').handlers[0]
handler.doRollover()


desktop_mode = False


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

        print(edits)

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

        if edits:
            # Apply trim
            trim = edits.get("trim", {})
            if "start_time" in trim:
                cmd.insert(1, "-ss")
                cmd.insert(2, str(trim["start_time"]))
            if "end_time" in trim:
                cmd.insert(3, "-to")
                cmd.insert(4, str(trim["end_time"]))


            # Build audio filter chain
            filters = []

            if "volume" in edits:
                volume = edits['volume'] 
                filters.append(f"volume={max(0.5, min(volume, 5))}")

            if "speed" in edits:
                speed = edits["speed"]
                filters.append(f"atempo={max(0.5, min(speed, 2))}")

            if filters:
                cmd += ["-af", ",".join(filters)]

            # Metadata injection (only if desktop_mode)
            if desktop_mode and "metadata" in edits:
                for key, value in edits["metadata"].items():
                    if key == "upload_date":
                        value = value[:10]
                    cmd += ["-metadata", f"{key}={value}"]


        cmd += ["-"]

        logger.debug("FFmpeg command: %s", " ".join(cmd))

        # print("FFmpeg command:", " ".join(cmd))


        # Pipe output to response
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            return process.stdout
        except Exception as e:
            logger.error("FFmpeg failed with command: %s", " ".join(cmd))
            raise RuntimeError(f"Failed to stream with edits: {str(e)}")
