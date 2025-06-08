# SeekBeatServer.spec
# Run with: pyinstaller SeekBeatServer.spec

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import rest_framework

# Project paths
base_dir = os.path.abspath(".")
static_dir = os.path.join(base_dir, "static")
templates_dir = os.path.join(base_dir, "templates")

# Django apps to fully import
hidden_imports = collect_submodules("seekbeat") + \
                 collect_submodules("search") + \
                 collect_submodules("chrome_extension") + \
                 collect_submodules("desktop_lan_connect") + \
                 collect_submodules("stream")

# Data files (static, templates, .env, db, etc.)
datas = collect_data_files("seekbeat", includes=["*.html"]) + \
        collect_data_files("rest_framework", includes=["templates/**"]) + [
            (static_dir, "static"),
            (templates_dir, "templates"),
            (".env", "."),
            ("db.sqlite3", "."),
        ]

block_cipher = None
os.environ["DJANGO_SETTINGS_MODULE"] = "seekbeat.settings"

a = Analysis(
    ["seekbeat_start.py"],     
    pathex=[base_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports + ["config"],  # Ensure config.py is bundled
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,       
    a.zipfiles,       
    a.datas,          
    exclude_binaries=False,
    name="SeekBeatServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,     
    single_file=True,
)


