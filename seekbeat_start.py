import os
import sys
import signal
import socket
import pkgutil

# 1) Determine base directory depending on frozen status
if getattr(sys, "frozen", False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# 2) Add base_dir to system path so Django modules can be found
sys.path.insert(0, base_dir)

# 3) Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "seekbeat.settings")

# 4) Initialize Django
import django
django.setup()

# 5) Force-import all Django apps to ensure PyInstaller includes them
for pkg_name in ("seekbeat", "search", "chrome_extension", "desktop_lan_connect", "stream"):
    try:
        pkg = __import__(pkg_name, fromlist=["*"])
        for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            __import__(name)
    except Exception as e:
        print(f"Warning: could not import {pkg_name} -> {e}")

# 6) Force-include WSGI and middleware
import seekbeat.wsgi  # noqa
import seekbeat.middleware

# 7) Start Django server
from django.core.management import call_command
from config import get_local_ip  # Ensure this is bundled too

DEFAULT_PORT_RANGE = (8000, 9000)
DEFAULT_HOST = "0.0.0.0"


title = r"""

 ____            _    ____             _   
/ ___|  ___  ___| | _| __ )  ___  __ _| |_ 
\___ \ / _ \/ _ \ |/ /  _ \ / _ \/ _` | __|
 ___) |  __/  __/   <| |_) |  __/ (_| | |_ 
|____/ \___|\___|_|\_\____/ \___|\__,_|\__|


"""

def color(text, fg="green"):
    colors = {
        "black": "\033[30m","red": "\033[31m","green": "\033[32m",
        "yellow": "\033[33m","blue": "\033[34m","magenta": "\033[35m",
        "cyan": "\033[36m","white": "\033[37m","reset": "\033[0m"
    }
    return f"{colors.get(fg.lower(), '')}{text}{colors['reset']}"

def find_free_port(start=8000, end=9000):
    for port in range(start, end + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
    raise RuntimeError("❌ No free ports available.")

def graceful_exit(signum, frame):
    print(color("\n🛑 Server stopped by user.", "red"))
    sys.exit(0)

def start_server(host=DEFAULT_HOST):
    port = find_free_port(*DEFAULT_PORT_RANGE)
    os.environ["PORT"] = str(port)
    local_ip = get_local_ip()
    print(color(title, "blue"))
    print(color(f"🚀 Starting server on http://{host}:{port}", "green"))
    print(color(f"🚀 Access the app locally at http://localhost:{port}", "yellow"))
    print(color(f"🚀 Access the app on LAN at http://{local_ip}:{port}", "cyan"))

    # Start Django's development server
    call_command("runserver", f"{host}:{port}", use_reloader=False)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)
    try:
        start_server()
    except KeyboardInterrupt:
        print(color("\n🛑 Interrupted by user (KeyboardInterrupt).", "red"))
    except Exception as e:
        print(color(f"❌ Error: {e}", "red"))
