"""
SportIQ — Backend Configuration
Centralized settings for the FastAPI backend server.
"""

import os

# ── File Upload Settings ──────────────────────────────────────
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # 50MB

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".webm", ".mkv"}
ALLOWED_MIME_TYPES = {
    "video/mp4",
    "video/avi",
    "video/x-msvideo",
    "video/quicktime",
    "video/webm",
    "video/x-matroska",
}

# ── Directory Paths ───────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed")

# ── Supported Sports ─────────────────────────────────────────
SUPPORTED_SPORTS = ["cricket"]  # Football added next semester

# ── Cricket Shot Types ────────────────────────────────────────
CRICKET_SHOTS = [
    "cover_drive",
    "straight_drive",
    "pull_shot",
    "cut_shot",
    "sweep_shot",
    "defensive_block",
    "lofted_shot",
    "flick_shot",
    "other",
]

# ── MediaPipe Settings ────────────────────────────────────────
MODEL_COMPLEXITY = 1          # 0=Lite, 1=Full, 2=Heavy
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5
MAX_PROCESS_WIDTH = 1280
MAX_PROCESS_HEIGHT = 720

# ── API Settings ──────────────────────────────────────────────
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# ── CORS Settings ─────────────────────────────────────────────
# Allow all origins for development; restrict in production
CORS_ORIGINS = [
    "*",
]
