# seekbeat/config.py

import os
from pathlib import Path
from platformdirs import user_data_dir
from dotenv import load_dotenv
import socket
import sys
import os
import logging
logger = logging.getLogger('seekbeat')





load_dotenv(override=True)  # Load .env

# === Environment Flag ===
SEEKBEAT_ENV = os.getenv("SEEKBEAT_ENV", "desktop").lower()

IS_WEB = SEEKBEAT_ENV == "web"
IS_DESKTOP = SEEKBEAT_ENV == "desktop"
IS_DEV = SEEKBEAT_ENV == "dev"


# === App Name ===
APP_NAME = "SeekBeat"

# === Root Folder (for non-web apps) ===
APP_STORAGE_DIR = Path(user_data_dir(APP_NAME)) if IS_DESKTOP else Path(__file__).resolve().parent.parent

# === FFmpeg Path (Optional Override) ===
FFMPEG_DIR = Path(os.getenv("FFMPEG_DIR", APP_STORAGE_DIR / "ffmpeg"))

# === QR Codes (Desktop Only) ===
QR_DIR = APP_STORAGE_DIR / "qrcodes"

# === Song Storage (Desktop Only) ===
SONG_STORAGE_PATH = APP_STORAGE_DIR / "songs"

# === Logs ===
LOG_DIR = APP_STORAGE_DIR / "logs"
LOG_FILE = LOG_DIR / "seekbeat.log"

PORT = int(os.environ.get("PORT", 8010))


# === Optional Dev Paths (Only for local debugging)
if IS_DEV:
    DEV_ROOT = Path(__file__).resolve().parent.parent
    QR_DIR = DEV_ROOT / "SeekBeat" / "desktop_lan_connect" / "lan_utils" / "qrcodes"
    SONG_STORAGE_PATH = DEV_ROOT / "SeekBeat" / "desktop_lan_connect" / "lan_utils" / "songs"
    FFMPEG_DIR = DEV_ROOT / "SeekBeat" / "ffmpeg"
    LOG_DIR = DEV_ROOT / "SeekBeat" / "logs"
    LOG_FILE = LOG_DIR / "seekbeat.log"





def get_local_ip():
    try:
        # Connect to an external host just to get the IP, doesn't send data
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"
    


def get_resource_path(relative_path: str) -> str:
    """
    Returns the absolute path to a file located next to the .exe when frozen,
    or next to the script during development.
    """
    if getattr(sys, 'frozen', False):
        # If bundled by PyInstaller
        base_path = os.path.dirname(sys.executable)
    else:
        # When running as a normal Python script
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)





def load_api_key(key_name: str) -> str | None:
    path = get_resource_path("config/api.key")
    try:
        with open(path, 'r') as f:
            for line in f:
                # Skip empty lines and comments
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Parse key=value format
                if '=' in line:
                    name, value = line.split('=', 1)
                    if name.strip() == key_name:
                        return value.strip()
    except FileNotFoundError:
        print("API key config file not found.")
        logger.error("API key config file not found. for key:%s", key_name)
    return None
