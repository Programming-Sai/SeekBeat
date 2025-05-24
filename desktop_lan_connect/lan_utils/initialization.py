import json
import uuid
import qrcode
import socket
import os
import subprocess
from PIL import Image
from django.conf import settings




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
        self.qr_dir = r"c:\Users\pc\Desktop\Projects\SeekBeat\desktop_lan_connect\lan_utils\qrcodes"
        self.port = 3001
        self.fillColor = "red"
        self.backColor = "black"
        os.makedirs(self.qr_dir, exist_ok=True)
        self.session_store = os.path.join(self.qr_dir, "active_sessions.json")
        if not os.path.isfile(self.session_store):
            with open(self.session_store, "w") as f:
                json.dump({}, f)


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
        finally:
            s.close()
        return ip


    def generate_stylized_qr(self, data: str, filename: str, logo_path: str = None) -> str:
        """
        Generate a high-error-correction QR code containing `data`, optionally
        overlay a logo at its center, and save to disk.

        Args:
            data (str): The string payload to encode (often JSON).
            filename (str): The filename (PNG) under qr_dir to save.
            logo_path (str, optional): Filesystem path to a logo image.

        Returns:
            str: The full path to the saved QR code image.
        """
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color=self.fillColor, back_color=self.backColor).convert("RGB")

        if logo_path and os.path.exists(logo_path):
            logo = Image.open(logo_path)
            box_size = img.size[0] // 4
            logo = logo.resize((box_size, box_size))

            pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
            img.paste(logo, pos, mask=logo if logo.mode == "RGBA" else None)

        save_path = os.path.join(self.qr_dir, filename)
        img.save(save_path)
        return save_path





    def has_active_session(self) -> bool:
        """
        Check if there is currently an active session stored on disk.

        Returns:
            bool: True if `active_sessions.json` contains any keys, False otherwise.
        """
        if not os.path.isfile(self.session_store):
            return False
        with open(self.session_store, "r") as f:
            sessions = json.load(f)
            return bool(sessions)  # True if any session exists







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
        if self.get_session_data()['access_code'] == access_code:
            if qr_path and os.path.isfile(qr_path):
                os.remove(qr_path)

            if os.path.isfile(self.session_store):
                with open(self.session_store, "w") as f:
                    f.write(json.dumps({}))
            
            return {"message": "Session terminated."}
        else:
            raise PermissionError("Invalid access code.")

                



    def save_session(self, access_code: str, ip: str, port: int, qr_path: str) -> None:
        """
        Persist the active session’s details to disk.

        Args:
            access_code (str): UUID string for session authorization.
            ip (str): Host LAN IP address.
            port (int): Port number for client connections.
            qr_path (str): Full path to the QR code PNG.
        """
        with open(self.session_store, "r+") as f:
            sessions = json.load(f)
            sessions = {"access_code":access_code, "ip": ip, "port": port, "qr_path": qr_path}
            f.seek(0)
            json.dump(sessions, f)
            f.truncate()





    def get_session_data(self) -> dict:
        """
        Read the session_store JSON and return its contents.

        Returns:
            dict: { "access_code": ..., "ip": ..., "port": ..., "qr_path": ... }
        """
        with open(self.session_store, "r") as f:
            return json.loads(f.read())






    def initialize_session(self, allow_override: bool = False) -> tuple[str, str]:
        """
        Start a new LAN session by generating a fresh access code and QR code.

        Args:
            allow_override (bool): If True, kill any existing session first.

        Returns:
            tuple: (qr_path: str, access_code: str)

        Raises:
            Exception: If a session already exists and override is False.
        """
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
        logo_path = os.path.join(self.qr_dir, "logo.png")
        qr_path = self.generate_stylized_qr(json.dumps(wifi_payload), filename, logo_path=logo_path)

        self.save_session(access_code, ip, self.port, qr_path)
        return qr_path, access_code
