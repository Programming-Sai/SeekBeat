import os
import signal
import socket
import subprocess
import sys

def find_free_port(start=8000, end=9000):
    for port in range(start, end+1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError("No free port found in range.")


def graceful_exit(signum, frame):
    print("\n🛑 Server stopped by user (Ctrl+C or termination signal).")
    sys.exit(0)

if __name__ == "__main__":
    # Handle Ctrl+C or kill
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)

    try:
        port = find_free_port()
        os.environ["PORT"] = str(port)
        print(f"✅ Starting server on port {port}...")
        subprocess.run([sys.executable, "manage.py", "runserver", f"0.0.0.0:{port}"])
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user (KeyboardInterrupt). Exiting...")
    except Exception as e:
        print(f"❌ Error: {e}")