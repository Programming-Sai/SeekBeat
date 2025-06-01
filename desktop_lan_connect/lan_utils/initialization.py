import json
import shutil
import uuid
import qrcode
import socket
import os
from PIL import Image, ImageDraw, ImageColor
from config import QR_DIR, PORT
from django.contrib.staticfiles import finders
import logging

logger = logging.getLogger('seekbeat')
handler = logging.getLogger('seekbeat').handlers[0]
handler.doRollover()


class LANCreator:
    """
    Manages a single local-network “session” by generating a QR code that
    encodes connection details and by persisting session state to disk.

    Attributes:
        qr_dir (str): Filesystem path where QR codes and session JSON are stored.
        port (int): TCP port number for clients to connect on.
        fillColor (str): Color used to draw QR modules.
        backColor (str): Background color for the QR image.
        session_store (str): Path to JSON file tracking the active session.
    """
    def __init__(self):
        """
        Initialize storage directories and session file. Creates `qr_dir` if necessary,
        then ensures `active_sessions.json` exists (initially empty).
        """
        # self.qr_dir = os.path.join(settings.BASE_DIR, 'lan_utils', 'qrcodes')
        self.qr_dir = QR_DIR
        self.port = PORT
        self.fillColor = "black"
        self.backColor = "white"
        os.makedirs(self.qr_dir, exist_ok=True)
        self.session_store = os.path.join(self.qr_dir, "active_sessions.json")
        if not os.path.isfile(self.session_store):
            with open(self.session_store, "w") as f:
                json.dump({}, f)
        logger.info("LANCreator initialized with QR directory: %s", self.qr_dir)


    def get_lan_ip(self) -> str:
        """
        Determine the host’s LAN IP address by opening a UDP socket to a public DNS.
        Returns:
            str: The local IP address (e.g. "192.168.0.5").
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            logger.debug("LAN IP detected: %s", ip)
        finally:
            s.close()
        return ip


    def generate_stylized_qr(self, data: str, filename: str, logo_path: str = None, fill_color: str = "black", back_color: str = "white") -> str:
        """
        Generate a high-error-correction QR code containing `data`, optionally
        overlay a circular logo at its center, and save to disk.

        Supports named colors and hex color codes (e.g., '#222222') for fill and background.

        Args:
            data (str): The string payload to encode (often JSON).
            filename (str): The filename (PNG) under qr_dir to save.
            logo_path (str, optional): Filesystem path to a transparent PNG logo image to overlay.
            fill_color (str, optional): Color for QR modules (default 'black'). Accepts named colors or hex.
            back_color (str, optional): Background color (default 'white'). Accepts named colors or hex.

        Returns:
            str: The full path to the saved QR code image.
        """
        logger.info("Generating QR code for data: %s", data)
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        self.fillColor = fill_color
        self.backColor = back_color
        print("Color Issues", self.backColor)

        img = qr.make_image(fill_color=self.fillColor, back_color=self.backColor).convert("RGB")

        if logo_path and os.path.exists(logo_path):
            try:
                logger.debug("Adding logo overlay from: %s", logo_path)
                logo = Image.open(logo_path).convert("RGBA")
                box_size = img.size[0] // 4
                padding = box_size // 10  # 10% padding
                inner_size = box_size - 2 * padding
                logo = logo.resize((inner_size, inner_size), Image.LANCZOS)


                # Step 2: Create circular background
                circle = Image.new("RGBA", (box_size, box_size), (0, 0, 0, 0))  # fully transparent
                draw = ImageDraw.Draw(circle)
                draw.ellipse((0, 0, box_size, box_size), fill=self._parse_color(back_color) + (255,))

                # Step 3: Paste logo onto circle, centered
                circle.paste(logo, (padding, padding), logo)


                # Step 4: Paste circular logo onto QR code
                pos = ((img.size[0] - box_size) // 2, (img.size[1] - box_size) // 2)
                img.paste(circle, pos, circle)
            except Exception as e:
                logger.error("Failed to apply logo overlay: %s", str(e), exc_info=True)


        save_path = os.path.join(self.qr_dir, filename)
        img.save(save_path)
        logger.info("QR code saved to %s", save_path)
        return save_path


    def _parse_color(self, color_str: str, default: str = "white") -> tuple:
        """
        Parse a color string into an RGB tuple. Supports named colors and hex codes.
        Returns default color (as string) if invalid or empty.
        """
        if not color_str:
            color_str = default
        try:
            rgb = ImageColor.getrgb(color_str)
            logger.debug("Parsed color %s to RGB %s", color_str, rgb)
            return rgb
        except ValueError:
            logger.error("Invalid color string: '%s'", color_str)
            raise



    def has_active_session(self) -> bool:
        """
        Check if there is currently an active session stored on disk.

        Returns:
            bool: True if `active_sessions.json` contains any keys, False otherwise.
        """
        if not os.path.isfile(self.session_store):
            logger.debug("Session store does not exist.")
            return False
        with open(self.session_store, "r") as f:
            sessions = json.load(f)
            active = bool(sessions)
            logger.debug("Session check: %s", active)
            return active







    def terminate_session(self, qr_path: str, access_code: str) -> dict:
        """
        End the active session if the provided `access_code` matches.
        Deletes the stored QR file and clears session_store JSON.

        Args:
            qr_path (str): Full path to the QR code PNG to delete.
            access_code (str): The session’s UUID access code.

        Returns:
            dict: {"message": "Session terminated."}

        Raises:
            PermissionError: If the access_code is invalid.
        """
        try:
            if self.qr_dir and os.path.isdir(self.qr_dir):
                shutil.rmtree(self.qr_dir)
                os.makedirs(self.qr_dir, exist_ok=True)
                self.session_store = os.path.join(self.qr_dir, "active_sessions.json")
                with open(self.session_store, "w") as f:
                    json.dump({}, f)
                logger.info("All sessions terminated and directory reset.")
            else:
                raise FileNotFoundError(f"{self.qr_dir} does not exist.")
        except Exception as e:
            logger.error("Failed to terminate all sessions: %s", str(e), exc_info=True)

                



    def save_session(self, access_code: str, ip: str, port: int, qr_path: str) -> None:
        """
        Persist the active session’s details to disk.

        Args:
            access_code (str): UUID string for session authorization.
            ip (str): Host LAN IP address.
            port (int): Port number for client connections.
            qr_path (str): Full path to the QR code PNG.
        """
        try:
            session_data = {
                "access_code": access_code,
                "ip": ip,
                "port": port,
                "qr_path": qr_path
            }
            with open(self.session_store, "w") as f:
                json.dump(session_data, f)
            logger.info("Session saved: %s", session_data)
        except Exception as e:
            logger.error("Failed to save session: %s", str(e), exc_info=True)






    def get_session_data(self) -> dict:
        """
        Read the session_store JSON and return its contents.

        Returns:
            dict: { "access_code": ..., "ip": ..., "port": ..., "qr_path": ... }
        """
        try:
            with open(self.session_store, "r") as f:
                data = json.load(f)
                logger.debug("Retrieved session data: %s", data)
                return data
        except Exception as e:
            logger.error("Failed to read session data: %s", str(e), exc_info=True)
            raise






    def initialize_session(self, allow_override: bool = False, fill_color: str = "black", back_color: str = "white", theme: str = "dark") -> tuple[str, str]:
        """
        Start a new LAN session by generating a fresh access code and QR code.

        Supports customizing the QR code's fill and background colors via named colors or hex codes.

        Args:
            allow_override (bool): If True, terminate any existing session before starting a new one.
            fill_color (str, optional): Color for QR modules (default 'black').
            back_color (str, optional): Background color (default 'white').
            theme (str, optional): UI theme, e.g., 'dark' or 'light' (default 'dark').

        Returns:
            tuple: (qr_path: str, access_code: str)

        Raises:
            Exception: If a session already exists and override is False.
        """
        logger.info("Initializing new LAN session (override=%s)...", allow_override)
        ip = self.get_lan_ip()
        
        # Check if any session is already active
        if self.has_active_session():
            if not allow_override:
                raise Exception("An active session already exists.")
            else:
                self.terminate_all_sessions()

        access_code = str(uuid.uuid4())
        wifi_payload = {"access_code": access_code, "host_ip": ip, "port": self.port}

        filename = f"lan_session_{access_code}.png"
        logo_path = finders.find("seekbeat-favicon-light.png") if theme == "dark" else finders.find("seekbeat-favicon-dark.png")
        qr_path = self.generate_stylized_qr(
            json.dumps(wifi_payload),
            filename,
            logo_path=logo_path,
            fill_color=fill_color,
            back_color=back_color,
        )

        self.save_session(access_code, ip, self.port, qr_path)
        logger.info("New LAN session initialized: %s", access_code)
        return qr_path, access_code


    def terminate_all_sessions(self):
        """
        Terminate all existing LAN sessions by clearing the QR code directory
        and resetting the session store.

        Raises:
            FileNotFoundError: If the QR code directory does not exist.
        """
        try:
            logger.info("Terminating all LAN sessions.")
            if self.qr_dir and os.path.isdir(self.qr_dir):
                shutil.rmtree(self.qr_dir)
                os.makedirs(self.qr_dir, exist_ok=True)
                self.session_store = os.path.join(self.qr_dir, "active_sessions.json")
                if not os.path.isfile(self.session_store):
                    with open(self.session_store, "w") as f:
                        json.dump({}, f)
                logger.info("All sessions terminated and directory reset.")
            else:
                raise FileNotFoundError(f"{self.qr_dir} does not exist.")
        except Exception as e:
            logger.error("Failed to terminate sessions: %s", str(e), exc_info=True)
