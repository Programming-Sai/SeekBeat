import os
import signal
import socket
import subprocess
import sys
import socket
from config import get_local_ip


DEFAULT_PORT_RANGE = (8000, 9000)
DEFAULT_HOST = "0.0.0.0"


def color(text, fg="green"):
    colors = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "reset": "\033[0m"
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
    print(color(f"🚀 Starting server on http://{host}:{port}", "green"))
    print(color(f"🚀 Access the app locally at http://localhost:{port}", "yellow"))
    print(color(f"🚀 Access the app on LAN at http://{local_ip}:{port}", "cyan"))
    subprocess.run([sys.executable, "manage.py", "runserver", f"{host}:{port}"])


if __name__ == "__main__":
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)

    try:
        start_server()
    except KeyboardInterrupt:
        print(color("\n🛑 Interrupted by user (KeyboardInterrupt).", "red"))
    except Exception as e:
        print(color(f"❌ Error: {e}", "red"))
