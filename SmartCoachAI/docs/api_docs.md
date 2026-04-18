# SportIQ — API Documentation

## Base URL

- **Local:** `http://localhost:8000`
- **Production:** `https://sportiq-backend.onrender.com`

## Interactive Docs

FastAPI auto-generates interactive API docs:
- **Swagger UI:** `{base_url}/docs`
- **ReDoc:** `{base_url}/redoc`

---

## Endpoints

### `GET /` — Root

Returns API welcome message.

**Response:**
```json
{
  "project": "SportIQ — AI-Powered Cricket Performance Analyzer",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

### `GET /health` — Health Check

Used by deployment platforms to verify the service is alive.

**Response:**
```json
{
  "status": "healthy",
  "service": "sportiq-backend"
}
```

---

### `GET /api/v1/status` — API Status & Capabilities

Returns supported features and limits.

**Response:**
```json
{
  "status": "online",
  "api_version": "v1",
  "project": "SportIQ — Cricket Shot Analyzer",
  "supported_sports": ["cricket"],
  "cricket_shot_types": [
    "cover_drive", "straight_drive", "pull_shot", "cut_shot",
    "sweep_shot", "defensive_block", "lofted_shot", "flick_shot", "other"
  ],
  "max_file_size_mb": 50,
  "allowed_formats": [".mp4", ".avi", ".mov", ".webm", ".mkv"]
}
```

---

### `POST /api/v1/upload` — Upload & Process Video

Upload a cricket video for AI pose estimation.

**Content-Type:** `multipart/form-data`

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | ✅ | Video file (.mp4, .avi, .mov, .webm, .mkv) |
| `sport` | string | ❌ | Sport type. Default: `cricket` |
| `shot_type` | string | ❌ | Shot type. Default: `other` |

**Success Response (200):**
```json
{
  "status": "success",
  "message": "Video processed successfully with pose estimation",
  "data": {
    "video_url": "/api/v1/video/pose_filename.mp4",
    "keypoints_url": "/api/v1/keypoints/keypoints_filename.json",
    "sport": "cricket",
    "shot_type": "cover_drive",
    "stats": {
      "total_frames": 150,
      "frames_with_pose": 142,
      "detection_rate_percent": 94.7,
      "processing_time_seconds": 12.5,
      "original_resolution": "1920x1080",
      "processed_resolution": "1280x720",
      "fps": 30.0,
      "duration_seconds": 5.0
    }
  }
}
```

**Error Responses:**

| Code | Error | Description |
|------|-------|-------------|
| 400 | `unsupported_sport` | Sport type not supported |
| 400 | `invalid_file_type` | File extension not allowed |
| 413 | `file_too_large` | File exceeds 50MB limit |
| 500 | `processing_failed` | ML processing error |

---

### `GET /api/v1/video/{filename}` — Get Processed Video

Serves a processed video file with skeleton overlay.

**Parameters:**
- `filename` (path) — Filename from upload response `video_url`

**Response:** Video file (`video/mp4`)

---

### `GET /api/v1/keypoints/{filename}` — Get Keypoints JSON

Serves keypoints JSON with pose landmark data.

**Parameters:**
- `filename` (path) — Filename from upload response `keypoints_url`

**Response:** JSON file with frame-by-frame keypoint data

---

## Usage Examples

### cURL

```bash
# Upload a video
curl -X POST "http://localhost:8000/api/v1/upload" \
  -F "file=@my_cricket_video.mp4" \
  -F "sport=cricket" \
  -F "shot_type=cover_drive"

# Check health
curl http://localhost:8000/health

# Get API status
curl http://localhost:8000/api/v1/status
```

### Python (requests)

```python
import requests

url = "http://localhost:8000/api/v1/upload"
files = {"file": open("cricket_video.mp4", "rb")}
data = {"sport": "cricket", "shot_type": "cover_drive"}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Processed video: {result['data']['video_url']}")
print(f"Detection rate: {result['data']['stats']['detection_rate_percent']}%")
```

### JavaScript (fetch)

```javascript
const formData = new FormData();
formData.append('file', videoFile);
formData.append('sport', 'cricket');

const response = await fetch('http://localhost:8000/api/v1/upload', {
  method: 'POST',
  body: formData,
});

const result = await response.json();
console.log(result.data.stats);
```
