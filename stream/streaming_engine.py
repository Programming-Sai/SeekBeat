"""
StreamingEngine Module

Provides a Django-friendly audio streaming engine using yt-dlp and FFmpeg.
Supports on-the-fly audio trimming, speed/volume adjustments, and ID3 metadata embedding (via Mutagen).
"""

import threading
import yt_dlp
import subprocess
import imageio_ffmpeg
import os
import tempfile
import requests
import uuid
import shutil
import logging
import urllib.parse
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, WXXX, error



logger = logging.getLogger('seekbeat')
handler = logging.getLogger('seekbeat').handlers[0]
handler.doRollover()


desktop_mode = True


class StreamingEngine:
    """
    Handles audio extraction, real-time streaming with FFmpeg, and metadata injection.
    """

    def __init__(self):
        """
        Initializes yt-dlp options and ensures an FFmpeg binary is available.
        """
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
        """
        Uses yt-dlp to fetch stream URL and basic metadata without downloading.

        Returns:
            dict: {stream_url, title, duration, thumbnail, source}
        """
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







    def stream_with_edits(self, input_src: str, edits: dict, duration: int):
        """
        Streams audio with optional edits and metadata injection.
        If edits are provided, performs a single FFmpeg pass with trimming, filters, converts to MP3,
        embeds metadata & cover art, then streams the file directly.
        Otherwise, pipes the raw stream through FFmpeg for real-time edits.

        Yields:
            bytes: Chunks of MP3 audio data.
        """
        try:
            print(edits)
            temp_cleanup_mp3 = temp_cleanup_jpg = None  

            # Real-time streaming via FFmpeg pipe
            cmd = [
                self.ffmpeg_path,
                "-nostdin",
                "-i", input_src,
                "-vn",  
                "-f", "mp3",  
                "-acodec", "libmp3lame",
                "-loglevel", "quiet"
            ]


            if edits and desktop_mode and "metadata" in edits:
                # One-pass transform + metadata
                cover = edits["metadata"].get("thumbnail")
                input_src, cover_path = self.inject_metadata(input_src, edits, cover)
                print("Metadata Enclosure")
                
                # Stream processed file
                with open(input_src, 'rb') as f:
                    while True:
                        chunk = f.read(8192)
                        if not chunk:
                            break
                        yield chunk

                temp_cleanup_mp3 = input_src
                temp_cleanup_jpg = cover_path
                return

            elif edits:
                # Apply trim
                trim = edits.get("trim", {})
                if "start_time" in trim and isinstance(trim["start_time"], (int, float)) and 0 <= trim["start_time"] <= duration:
                    cmd.insert(1, "-ss")
                    cmd.insert(2, str(trim["start_time"]))

                if "end_time" in trim and isinstance(trim["end_time"], (int, float)) and 0 <= trim["end_time"] <= duration:
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


            # ALWAYS preserve ID3 tags and metadata
            cmd += ["-map_metadata", "0", "-id3v2_version", "3", "-write_id3v1", "1", "-y", "-"]


            logger.debug("FFmpeg command: %s", " ".join(cmd))

            # Pipe output to response
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(process.stderr, "House of Cards")
            # return process.stdout
            # self.pipe_stream(process.stdout)
            yield from self.pipe_stream(process.stdout)

        except Exception as e:
            logger.error("FFmpeg failed with command: %s", " ".join(cmd))
            raise RuntimeError(f"Failed to stream with edits: {str(e)}")
        finally:
            def cleanup():
                """
                Deletes temporary files if they exist.
                """
                if temp_cleanup_mp3 and os.path.exists(temp_cleanup_mp3): os.remove(temp_cleanup_mp3)
                if temp_cleanup_jpg and os.path.exists(temp_cleanup_jpg): os.remove(temp_cleanup_jpg)
            threading.Thread(target=cleanup, daemon=True).start()




    def is_url(self, path_or_url):
        """
        Determines if the given string is a valid URL.
        """
        try:
            result = urllib.parse.urlparse(path_or_url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False


    def inject_metadata(self, input_url, edits, cover=None):
        """
        Applies trimming, speed, volume edits via FFmpeg, converts to MP3,
        downloads cover image, and embeds metadata and cover art.

        Returns:
            tuple: (mp3_path, cover_image_path)
        """
        print("Injection Commencing")

        # edits contains trim, speed, volume, metadata
        temp_dir = tempfile.mkdtemp()
        uid = uuid.uuid4().hex
        raw_mp3 = os.path.join(temp_dir, f"{uid}.mp3")

        # build ffmpeg command to apply trim, speed, volume and convert to mp3
        cmd = [self.ffmpeg_path, '-nostdin', "-loglevel", "quiet"]
        trim = edits.get('trim', {})
        if 'start_time' in trim:
            cmd += ['-ss', str(trim['start_time'])]
        cmd += ['-i', input_url]
        if 'end_time' in trim:
            cmd += ['-to', str(trim['end_time'])]
        cmd += ['-vn', '-acodec', 'libmp3lame', '-ab', '192k']
        filters = []
        if 'volume' in edits:
            v = max(0.5, min(edits['volume'], 5))
            filters.append(f"volume={v}")
        if 'speed' in edits:
            s = max(0.5, min(edits['speed'], 2))
            filters.append(f"atempo={s}")
        if filters:
            cmd += ['-af', ','.join(filters)]
        cmd += ['-y', raw_mp3]
        subprocess.run(cmd, check=True)


        # download cover if provided
        raw_jpg = None
        if cover and self.is_url(cover):
            resp = requests.get(cover); resp.raise_for_status()
            raw_jpg = os.path.join(temp_dir, f"{uid}.jpg")
            with open(raw_jpg, 'wb') as img: img.write(resp.content)


        # embed with mutagen
        try:
            audio = EasyID3(raw_mp3)
        except error:
            audio = EasyID3(raw_mp3)
        meta = edits.get('metadata', {})
        for tag in ['title','artist','album','date','genre']:
            if tag in meta:
                audio[tag] = meta[tag]
        audio.save(raw_mp3)
        id3 = ID3(raw_mp3)
        if raw_jpg:
            with open(raw_jpg, 'rb') as img:
                id3.delall("APIC")
                id3.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc=u"Cover Art",
                    data=img.read()
                ))
        if 'url' in meta:
            id3.delall("WXXX")
            id3.add(WXXX(
                encoding=3,
                desc=u"Official YouTube Link",
                url=meta['url']
            ))
        id3.save(raw_mp3)

        return raw_mp3, raw_jpg
    


    def pipe_stream(self, proc_stdout, chunk_size=8192):
        """
        Yields chunks from FFmpeg stdout pipe.
        """
        print("Streaming...")
        while True:
            chunk = proc_stdout.read(chunk_size)
            if not chunk:
                break
            yield chunk