"""
SportIQ — Video API Router
Handles video upload, processing, and serving endpoints.
"""

import os
import uuid
import shutil
import logging

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.config import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    ALLOWED_EXTENSIONS,
    UPLOAD_DIR,
    PROCESSED_DIR,
    SUPPORTED_SPORTS,
    CRICKET_SHOTS,
    API_PREFIX,
)
from backend.services.pose_service import PoseService

logger = logging.getLogger(__name__)

router = APIRouter(prefix=API_PREFIX, tags=["Video Processing"])

# Initialize the pose service
pose_service = PoseService()

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _validate_file_extension(filename: str) -> bool:
    """Check if the file has an allowed video extension."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@router.post("/upload", summary="Upload and process a cricket video")
async def upload_video(
    file: UploadFile = File(..., description="Video file to process"),
    sport: str = Form(default="cricket", description="Sport type"),
    shot_type: str = Form(default="other", description="Cricket shot type"),
):
    """
    Upload a cricket video for AI pose estimation.
    
    The video will be processed with MediaPipe to detect body pose landmarks,
    draw a skeleton overlay, and extract keypoint data.
    
    **Supported formats:** .mp4, .avi, .mov, .webm, .mkv  
    **Max file size:** 50MB  
    **Supported sports:** cricket (football coming next semester)
    
    Returns the URL of the processed video and processing statistics.
    """
    # ── Validate sport type ───────────────────────────────────
    if sport not in SUPPORTED_SPORTS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "unsupported_sport",
                "message": f"Sport '{sport}' is not supported. Supported: {SUPPORTED_SPORTS}",
            },
        )

    # ── Validate shot type ────────────────────────────────────
    if shot_type not in CRICKET_SHOTS:
        shot_type = "other"

    # ── Validate file extension ───────────────────────────────
    if not file.filename or not _validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_file_type",
                "message": f"File type not supported. Allowed: {list(ALLOWED_EXTENSIONS)}",
            },
        )

    # ── Save uploaded file to temp location ───────────────────
    unique_id = str(uuid.uuid4())[:8]
    ext = os.path.splitext(file.filename)[1].lower()
    temp_filename = f"{unique_id}_{file.filename}"
    temp_path = os.path.join(UPLOAD_DIR, temp_filename)

    try:
        # Stream file to disk (memory-efficient for large files)
        total_size = 0
        with open(temp_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)  # Read 1MB at a time
                if not chunk:
                    break
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE_BYTES:
                    # Clean up and reject
                    buffer.close()
                    os.remove(temp_path)
                    raise HTTPException(
                        status_code=413,
                        detail={
                            "error": "file_too_large",
                            "message": f"File exceeds {MAX_FILE_SIZE_MB}MB limit. Got: {round(total_size / 1024 / 1024, 1)}MB",
                        },
                    )
                buffer.write(chunk)

        logger.info(f"Uploaded: {temp_filename} ({round(total_size / 1024 / 1024, 1)}MB)")

        # ── Process video with pose estimation ────────────────
        result = pose_service.process_cricket_video(
            input_path=temp_path,
            sport=sport,
        )

        # ── Build response ────────────────────────────────────
        response = {
            "status": "success",
            "message": "Video processed successfully with pose estimation",
            "data": {
                "video_url": f"{API_PREFIX}/video/{result['output_video_filename']}",
                "keypoints_url": (
                    f"{API_PREFIX}/keypoints/{result['keypoints_filename']}"
                    if result.get("keypoints_filename")
                    else None
                ),
                "sport": sport,
                "shot_type": shot_type,
                "stats": {
                    "total_frames": result["total_frames"],
                    "frames_with_pose": result["frames_with_pose"],
                    "detection_rate_percent": result["detection_rate"],
                    "processing_time_seconds": result["processing_time_seconds"],
                    "original_resolution": result["video_info"]["original_resolution"],
                    "processed_resolution": result["video_info"]["processed_resolution"],
                    "fps": result["video_info"]["fps"],
                    "duration_seconds": result["video_info"]["duration_seconds"],
                    "posture_error_rate": result.get("posture_error_rate", 0.0),
                },
            },
        }

        return JSONResponse(content=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "processing_failed",
                "message": f"Video processing failed: {str(e)}",
            },
        )
    finally:
        # Clean up uploaded input file
        pose_service.cleanup_input(temp_path)


@router.get("/video/{filename}", summary="Get processed video")
async def get_processed_video(filename: str):
    """
    Serve a processed video file with skeleton overlay.
    
    The filename is returned in the upload response's `video_url` field.
    """
    try:
        video_path = pose_service.get_processed_video_path(filename)
        return FileResponse(
            path=video_path,
            media_type="video/mp4",
            filename=filename,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Video '{filename}' not found"},
        )


@router.get("/keypoints/{filename}", summary="Get keypoints JSON")
async def get_keypoints(filename: str):
    """
    Serve keypoints JSON file with pose landmark data.
    
    Contains frame-by-frame (x, y, z, visibility) for all 33 pose landmarks.
    """
    try:
        json_path = pose_service.get_keypoints_path(filename)
        return FileResponse(
            path=json_path,
            media_type="application/json",
            filename=filename,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": f"Keypoints file '{filename}' not found"},
        )


@router.get("/status", summary="API status and capabilities")
async def get_status():
    """
    Get the API status, supported sports, and shot types.
    """
    return {
        "status": "online",
        "api_version": "v1",
        "project": "SportIQ — Cricket Shot Analyzer",
        "supported_sports": SUPPORTED_SPORTS,
        "cricket_shot_types": CRICKET_SHOTS,
        "max_file_size_mb": MAX_FILE_SIZE_MB,
        "allowed_formats": list(ALLOWED_EXTENSIONS),
    }
