# Device Mini-Server Specification

This document outlines the expected behavior and implementation details of the mini-server that runs on a user's device (e.g., via a React Native app) to handle remote song transfers.

---

## 🎯 Purpose

The mini-server is responsible for:

- Receiving requests from the main server to upload a song file.
- Locating the requested song on the device using its saved path.
- Uploading the file to the main server's `/api/upload/` endpoint.
- Returning the file path to the main server for immediate streaming.

---

## 🔌 Endpoint

### `GET /transfer/<device_file_path>`

- **Description**: Uploads the song file located at `device_file_path` to the main server and returns the upload response.

- **Request Format**:  
  No request body. Just a GET call with the path.

- **Example**:

```

GET /transfer/music/song123.mp3

```

- **Response** (on success):

```json
{
  "message": "Song File uploaded successfully.",
  "path": "/media/audio/song123.mp3"
}
```

- **Response** (on failure):

  ```json
  {
    "error": "Upload failed",
    "details": "<error_message>"
  }
  ```

---

## 📤 Uploading to Main Server

- The mini-server should upload the file using a `POST` request to the main server:

  ```
  POST http://<main-server-ip>:<port>/api/device/<uuid:device_id>/songs/<uuid:song_id>/upload/
  ```

- The payload should include:

  - The file
  - (Optional) Metadata such as song title, device ID, etc.

- **Main server will return** the server-side file path (used for streaming).

---

## ⚙️ Notes

- Port used by the mini-server must be stored in the database (`Device.port`) during registration.
- The mini-server must have access to the actual filesystem location of the song.
- If the file path is invalid (moved/deleted), the mini-server must return an error.
- Devices should be encouraged to resync or re-register if their file paths change.

---

## 🔐 Security (Planned)

- Add authentication headers (e.g., access token).
- Validate device ownership before allowing uploads.
- Add CORS restrictions if needed.
