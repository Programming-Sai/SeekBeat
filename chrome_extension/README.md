## SeekBeat Chrome Extension Module

A lightweight Django app powering the SeekBeat Chrome extension’s “Save Song” feature.
It lets users capture YouTube video metadata for later download or streaming—no copy‐paste required.

---

### 🚀 Key Features

- **CRUD API** for captured videos (create, list, retrieve, delete)
- **UUID** primary keys for robust, unguessable IDs
- **DRF + drf-spectacular** for auto-generated, swagger-compatible docs

---

### 📦 Installation & Setup

```bash
# 1. Clone the repo & enter directory
git clone https://github.com/your-org/seekbeat.git
cd seekbeat

# 2. Create & activate virtualenv
python -m venv .seek-venv
source .seek-venv/bin/activate    # macOS/Linux
.seek-venv\Scripts\activate       # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add to INSTALLED_APPS in seekbeat/settings.py
    INSTALLED_APPS += ['chrome_extension']

# 5. Run migrations
python manage.py makemigrations chrome_extension
python manage.py migrate

# 6. Create a superuser (for admin)
python manage.py createsuperuser

# 7. Start server
python manage.py runserver
```

---

### 🔗 API Endpoints

All routes are prefixed under `/api/ext/` in the main project:

| Method | Path                   | Description                |
| ------ | ---------------------- | -------------------------- |
| GET    | `/api/ext/`            | List all captured videos   |
| POST   | `/api/ext/add`         | Add a new captured video   |
| GET    | `/api/ext/{id}/`       | Retrieve one by UUID       |
| DELETE | `/api/ext/{id}/delete` | Delete one by UUID         |
| DELETE | `/api/ext/delete-all`  | Delete all captured videos |

---

#### ▶️ Request & Response Examples

**Create**

```http
POST /api/ext/add
Content-Type: application/json
X-CSRFToken: <token>

{
  "title":       "Never Gonna Give You Up",
  "duration":    213,
  "uploader":    "Rick Astley",
  "thumbnail":   "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
  "webpage_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "upload_date": "20091024"
}
```

**Success (201)**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "title": "Never Gonna Give You Up",
  "duration": 213,
  "uploader": "Rick Astley",
  "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
  "webpage_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "upload_date": "20091024",
  "created_at": "2025-05-28T16:30:00Z"
}
```

---

**List**

```http
GET /api/ext/
Accept: application/json
```

**Success (200)**

```json
[
  {
    /* bookmark object as above */
  },
  {
    /* ... */
  }
]
```

---

**Retrieve**

```http
GET /api/ext/3fa85f64-5717-4562-b3fc-2c963f66afa6/
```

**Success (200)**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "title": "Never Gonna Give You Up",
  "duration": 213,
  "uploader": "Rick Astley",
  "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
  "webpage_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "upload_date": "20091024",
  "created_at": "2025-05-28T16:30:00Z"
}
```

**Delete**

```http
DELETE /api/ext/3fa85f64-5717-4562-b3fc-2c963f66afa6/delete
```

**Success (200)**

```json
{ "deleted": true }
```

**Delete All**

```http
DELETE /api/ext/delete-all
```

**Success (200)**

```json
{"deleted": n} //n => count of items in db
```

---

### 🔍 API Documentation

Auto-generated OpenAPI schema & Swagger UI:

- **Schema**: `GET /api/schema/`
- **Swagger UI**: `GET /api/docs/`

---

### 📑 Admin Interface

- Manage captures via Django Admin at `/admin/`
- Registered under **Bookmarks** with searchable fields: `title`, `uploader`.

---

### 👩‍💻 Frontend Integration Tips

1. **Capture current tab URL** in your content script
2. **Fetch metadata** via the Search API
3. **POST** metadata JSON to `/api/ext/add`
4. **Handle responses**: update UI, show toast on success/failure
5. **List & Delete**: use GET & DELETE endpoints to power your in-extension playlist UI

---

### 🤝 Contributing

1. Fork & branch from `develop`
2. Write tests for new functionality
3. Adhere to PEP8 & DRF best practices
4. Submit a pull request, referencing an issue if applicable
