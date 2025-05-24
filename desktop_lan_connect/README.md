# SeekBeat LAN Module

A self-hosted local-network (LAN) API for seamless device registration, song metadata CRUD, and MP3 file sharing over your home or office network—no cloud required. Integrate this with any desktop or mobile frontend to build a real-time, peer-to-peer music sharing and streaming experience.

---

## 🚀 Features

- **Session Management**: Spin up a LAN “session” protected by a UUID-based access code, shared via QR.
- **Device Lifecycle**: Register, reconnect, list, and disconnect devices securely.
- **Song Metadata**: Create, read, update, delete song records in bulk or individually.
- **File Upload**: Push MP3 files from a device; files are auto-stored and cleaned up on disconnect.
- **Extensible**: Ready for streaming/download, search, playlists, and more.

---

## 📋 Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Installation & Quickstart](#️-installation--quickstart)
3. [Authentication](#-authentication)
4. [Endpoints Reference](#-endpoints-reference)

   - Session
   - Device
   - Songs

5. [Error Codes & Responses](#️-error-codes--responses)

---

## 🔧 Prerequisites

- Python 3.9+
- Django 4.x
- Django REST Framework
- drf-spectacular
- Pillow, qrcode, jsonschema, django-ratelimit
- (Optional) Postman or curl for testing

---

## ⚙️ Installation & Quickstart

```bash
git clone https://github.com/Programming-Sai/SeekBeat.git
cd seekbeat
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Now your API is live at `http://localhost:8000/api/lan/`.

---

## 🔑 Authentication

1. **Start a session** → GET `/api/lan/session-start/`
2. Scan or read the returned `qr_path` and copy the `access_code` from its payload.
3. **All endpoints below** require:

```http
Access-Code: <YOUR-SESSION-UUID>
```

Absent or invalid → **403 Forbidden**.

---

## 📐 Endpoints Reference

### 1. Session Management

| Method | Path              | Description                                | Success                                 | Errors                |
| ------ | ----------------- | ------------------------------------------ | --------------------------------------- | --------------------- |
| GET    | `/session-start/` | Create a LAN session; returns QR and code. | 200 `{qr_path, access_code}`            | 400 (already exists)  |
| GET    | `/session-check/` | Is a session active?                       | 200 `{"active": true/false}`            | —                     |
| POST   | `/session-end/`   | Terminate the session                      | 200 `{"message":"Session terminated."}` | 400 (no session), 403 |

---

### 2. Device Management

> [!NOTE]
> All require `Access-Code` header.

| Method | Path                  | Description                              | Success                    | Errors                   |
| ------ | --------------------- | ---------------------------------------- | -------------------------- | ------------------------ |
| POST   | `/device-connect/`    | Register or update a device              | 200 `{device_id, message}` | 400 (name conflict), 403 |
| POST   | `/device-reconnect/`  | Reactivate a disconnected device         | 200 `{device_id, message}` | 400 (not found), 403     |
| POST   | `/device-disconnect/` | Disconnect device; keep or delete record | 200 `{message, device_id}` | 404 (not found), 403     |
| GET    | `/devices/`           | List all currently active devices        | 200 `{count, devices:[…]}` | 403                      |

---

### 3. Song Metadata & Files

## 🎵 Song Metadata & File Endpoints

> [!NOTE] > **All song paths include** `<device_uuid>` in the URL and **require** `Access-Code`.

|     Method | Path                                             | Description                                                  |
| ---------: | ------------------------------------------------ | ------------------------------------------------------------ |
|    **GET** | `/device/<device_uuid>/songs`                    | List all songs for this device.                              |
| **DELETE** | `/device/<device_uuid>/songs`                    | Delete _all_ songs (metadata + files) for this device.       |
|   **POST** | `/device/<device_uuid>/songs/bulk_add`           | Bulk-create many songs. Body: Array of song-objects.         |
|   **POST** | `/device/<device_uuid>/songs/add`                | Create a single song. Body: single song-object.              |
|  **PATCH** | `/device/<device_uuid>/songs/<song_uuid>`        | Update a song’s metadata. Body: partial song-object.         |
| **DELETE** | `/device/<device_uuid>/songs/<song_uuid>`        | Delete one song (metadata + file).                           |
|   **POST** | `/device/<device_uuid>/songs/<song_uuid>/upload` | Upload the MP3 file for that song. Form-data: `file` (.mp3). |

#### a. List or Delete All Songs

```
GET    /device/<device_uuid>/songs
DELETE /device/<device_uuid>/songs
```

- **GET** → `200 [{song_profile}, …]`
- **DELETE** → `200 {"message":…}`

#### b. Bulk Add Songs

```
POST /device/<device_uuid>/songs/bulk_add
Content-Type: application/json
Body: [ {title, artist, duration_seconds, file_size_kb, file_format}, … ]
```

- **201** `{"added": <n>}`

#### c. Add Single Song

```
POST /device/<device_uuid>/songs/add
Content-Type: application/json
Body: {title, artist, duration_seconds, file_size_kb, file_format}
```

- **200** `{"song_id": "<uuid>", "message":…}`

#### d. Update or Delete One Song

```
PATCH  /device/<device_uuid>/songs/<song_uuid>
Body: { any subset of metadata fields }
→ 200 {"message":…}

DELETE /device/<device_uuid>/songs/<song_uuid>
→ 200 {"message":…}
```

#### e. Upload Song File

```
POST /device/<device_uuid>/songs/<song_uuid>/upload
Content-Type: multipart/form-data
Body: file=(.mp3 only)
```

- **201** `{"message":…,"path":…}`

---

## ⚠️ Error Codes & Responses

|      Status | Meaning                          | Example Body                      |
| ----------: | -------------------------------- | --------------------------------- |
| **200/201** | Success                          | `{"…":…}`                         |
|     **400** | Bad request / validation failure | `{"error":"<details>"}`           |
|     **403** | Forbidden – invalid/missing code | `{"error":"Invalid Access-Code"}` |
|     **404** | Not found – device/song missing  | `{"error":"Device not found"}`    |
|     **500** | Internal server error            | `{"error":"<exception message>"}` |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Submit a pull request with tests & docs
4. Enjoy the jam session! 🎶

---
