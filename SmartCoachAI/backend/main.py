"""
SportIQ — FastAPI Application
Main entry point for the backend API server.
Serves the video processing pipeline and static processed files.
"""

import os
import sys
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Add project root to sys.path for ml module imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import CORS_ORIGINS, PROCESSED_DIR, UPLOAD_DIR
from backend.routers.video import router as video_router

# ── Logging Setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sportiq")

# ── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title="SportIQ API",
    description=(
        "🏏 **SportIQ — AI-Powered Cricket Performance Analyzer**\n\n"
        "Upload a cricket video and get AI pose estimation with skeleton overlay.\n\n"
        "**Features:**\n"
        "- MediaPipe pose detection (33 body landmarks)\n"
        "- Skeleton overlay visualization\n"
        "- Keypoint extraction to JSON\n"
        "- Cricket-specific joint angle analysis\n\n"
        "**Stack:** FastAPI + MediaPipe + OpenCV\n\n"
        "Built by Team SportIQ 🚀"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Ensure Directories Exist ─────────────────────────────────
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Include Routers ───────────────────────────────────────────
app.include_router(video_router)


# ── Root & Health Endpoints ───────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    """API root — welcome message and links."""
    return {
        "project": "SportIQ — AI-Powered Cricket Performance Analyzer",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api_status": "/api/v1/status",
        "team": "Team SportIQ",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring and deployment verification."""
    return {
        "status": "healthy",
        "service": "sportiq-backend",
    }


# ── Startup / Shutdown Events ────────────────────────────────
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("=" * 60)
    logger.info("🏏 SportIQ API Starting Up...")
    logger.info(f"   Upload dir: {UPLOAD_DIR}")
    logger.info(f"   Processed dir: {PROCESSED_DIR}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown — cleanup temp files."""
    logger.info("🛑 SportIQ API Shutting Down...")
    # Clean up uploaded files (processed files are kept)
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            try:
                os.remove(os.path.join(UPLOAD_DIR, f))
            except Exception:
                pass
    logger.info("Cleanup complete. Goodbye!")
