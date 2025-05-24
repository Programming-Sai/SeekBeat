## SeekBeat LAN API

A simple, self-hosted local-network (LAN) API for device registration, song metadata management, and file uploads. Perfect for integrating into desktop or mobile front-ends that stream or share music over your local network without an external server.

---

### 🔑 Authentication

All device- and song-related endpoints require a valid `Access-Code` header, obtained when you start a LAN session.

```http
Access-Code: 123e4567-e89b-12d3-a456-426614174000
```

---

## 📡 Session Management

| Method | Endpoint          | Description                                               |
| ------ | ----------------- | --------------------------------------------------------- |
| GET    | `/session-start/` | Start a new session. Returns `{"qr_path": "<png_path>"}`. |
| GET    | `/session-check/` | Check if a session is active. Returns `{"active": true}`. |
| POST   | `/session-end/`   | Terminate session. Requires `Access-Code`.                |

---

## 🖥️ Device Management

### 1. Register or Update a Device

```http
POST /device-connect/
Headers: Access-Code
Content-Type: application/json

{
  "device_name": "My Laptop",
  "os_version": "Windows 11",
  "ram_mb": 8192,
  "storage_mb": 512000,
  "device_id": "<optional-UUID>"
}
```

**Response**

```json
{ "device_id": "<UUID>", "message": "My Laptop registered" }
```

### 2. Reconnect a Device

```http
POST /device-reconnect/
Headers: Access-Code
Content-Type: application/json

{ "device_id": "<UUID>" }
```

**Response**

```json
{ "device_id": "<UUID>", "message": "My Laptop reconnected" }
```

### 3. Disconnect a Device

```http
POST /device-disconnect/
Content-Type: application/json

{
  "device_id": "<UUID>",
  "keep_data": true     // or false to delete device record
}
```

**Response**

```json
{ "message": "My Laptop disconnected", "device_id": "<UUID>" }
```

### 4. List Active Devices

```http
GET /devices/
Headers: Access-Code
```

**Response**

```json
{
  "count": 2,
  "devices": [
    {
      "device_id": "<UUID>",
      "device_name": "My Laptop",
      "os_version": "Windows 11",
      "ram_mb": 8192,
      "storage_mb": 512000,
      "last_seen": "2025-05-24T10:00:00Z"
    },
    …
  ]
}
```

---

## 🎵 Song Metadata & File Management

_All song endpoints use the device’s UUID in the URL path._

### 1. List or Delete All Songs

```http
GET  /device/<device_uuid>/songs
DELETE /device/<device_uuid>/songs
```

- **GET** returns an array of song objects
- **DELETE** removes all songs and their files

### 2. Bulk Add Songs

```http
POST /device/<device_uuid>/songs/bulk_add
Content-Type: application/json

[
  {
    "title": "Blinding Lights",
    "artist": "The Weeknd",
    "duration_seconds": 200,
    "file_size_kb": 4300,
    "file_format": "mp3"
  },
  …
]
```

**Response**

```json
{ "added": 5 }
```

### 3. Add a Single Song

```http
POST /device/<device_uuid>/songs/add
Content-Type: application/json

{
  "title": "Sunflower",
  "artist": "Post Malone",
  "duration_seconds": 158,
  "file_size_kb": 3900,
  "file_format": "mp3"
}
```

### 4. Update or Delete One Song

```http
PATCH  /device/<device_uuid>/songs/<song_uuid>
DELETE /device/<device_uuid>/songs/<song_uuid>
```

- **PATCH** accepts a partial metadata object
- **DELETE** removes that song record and its file

### 5. Upload a Song File

```http
POST /device/<device_uuid>/songs/<song_uuid>/upload
Content-Type: multipart/form-data
Body: file=(your .mp3 file)
```

**Response**

```json
{ "message": "Song file uploaded successfully.", "path": "/…/song_<uuid>.mp3" }
```
