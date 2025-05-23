import json
import uuid
import qrcode
import socket
import os
import subprocess
from PIL import Image
from django.conf import settings

# Elevate for running with admin privileges on Windows (pip install elevate)
# from elevate import elevate


class LANCreator:
    def __init__(self):
        # self.qr_dir = os.path.join(settings.BASE_DIR, 'lan_utils', 'qrcodes')
        self.qr_dir = r"c:\Users\pc\Desktop\Projects\SeekBeat\desktop_lan_connect\lan_utils\qrcodes"
        self.port = 3001
        self.fillColor = "pink"
        self.backColor = "black"
        os.makedirs(self.qr_dir, exist_ok=True)


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

    
    def terminate_session(self, qr_path, access_code):
        if qr_path and os.path.isfile(qr_path):
            os.remove(qr_path)
        
        # Find a way yes the access_code as invalid.


    def initialize_session(self):
        # 1. Create and start the hotspot
        # self.create_and_start_hotspot()

        # 2. Get LAN IP (likely the IP of the hosted network interface)
        ip = self.get_lan_ip()
        access_code = str(uuid.uuid4())

        # 3. Prepare WiFi QR Code payload using WIFI standard format
        # This format is compatible with Android/iOS QR code scanners to auto-connect to WiFi:
        wifi_payload = {"access_code": access_code, "host_ip": ip,'port': self.port}
        

        filename = f"lan_session_{access_code}.png"
        logo_path = os.path.join(self.qr_dir, "logo.png")
        qr_path = self.generate_stylized_qr(json.dumps(wifi_payload), filename, logo_path=logo_path)

        return qr_path, access_code
        
