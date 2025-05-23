import json
import uuid
import qrcode
import socket
import os
import subprocess
from PIL import Image
from django.conf import settings




class LANCreator:
    def __init__(self):
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


    def get_lan_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip

    def generate_stylized_qr(self, data, filename, logo_path=None):
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

    def has_active_session(self):
        if not os.path.isfile(self.session_store):
            return False
        with open(self.session_store, "r") as f:
            sessions = json.load(f)
            return bool(sessions)  # True if any session exists

    def terminate_session(self, qr_path, access_code):
        if self.get_session_data()['access_code'] == access_code:
            if qr_path and os.path.isfile(qr_path):
                os.remove(qr_path)

            if os.path.isfile(self.session_store):
                with open(self.session_store, "w") as f:
                    f.write(json.dumps({}))
            
            return {"message": "Session terminated."}
        else:
            raise PermissionError("Invalid access code.")

                
    def save_session(self, access_code, ip, port, qr_path):
        with open(self.session_store, "r+") as f:
            sessions = json.load(f)
            sessions = {"access_code":access_code, "ip": ip, "port": port, "qr_path": qr_path}
            f.seek(0)
            json.dump(sessions, f)
            f.truncate()

    def get_session_data(self):
        with open(self.session_store, "r") as f:
            return json.loads(f.read())



    def initialize_session(self, allow_override=False):
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
