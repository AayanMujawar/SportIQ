"""
SportIQ — Video I/O Utilities
Handles video loading, saving, and metadata extraction using OpenCV.
"""

import cv2
import os
import logging

logger = logging.getLogger(__name__)


def get_video_info(video_path: str) -> dict:
    """
    Extract metadata from a video file.
    
    Args:
        video_path: Path to the video file.
        
    Returns:
        Dictionary with video metadata (fps, width, height, total_frames, duration).
        
    Raises:
        FileNotFoundError: If the video file doesn't exist.
        ValueError: If the video file can't be opened.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    info = {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "duration_seconds": 0.0,
    }

    if info["fps"] > 0:
        info["duration_seconds"] = round(info["total_frames"] / info["fps"], 2)

    cap.release()
    logger.info(
        f"Video info: {info['width']}x{info['height']} @ {info['fps']}fps, "
        f"{info['total_frames']} frames, {info['duration_seconds']}s"
    )
    return info


def create_video_writer(output_path: str, fps: float, width: int, height: int) -> cv2.VideoWriter:
    """
    Create an OpenCV VideoWriter with H.264 codec for web compatibility.
    Falls back to mp4v if H.264 is not available.
    
    Args:
        output_path: Path for the output video file.
        fps: Frames per second.
        width: Frame width in pixels.
        height: Frame height in pixels.
        
    Returns:
        Configured cv2.VideoWriter instance.
    """
    # Try H.264 first (best for web playback)
    # On many systems, 'avc1' or 'H264' might work
    codecs_to_try = ['avc1', 'H264', 'mp4v', 'XVID']

    for codec in codecs_to_try:
        fourcc = cv2.VideoWriter_fourcc(*codec)
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if writer.isOpened():
            logger.info(f"Using codec: {codec} for output video")
            return writer
        writer.release()

    # Final fallback
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    logger.warning("Falling back to mp4v codec")
    return writer


def resize_frame(frame, max_width: int = 1280, max_height: int = 720):
    """
    Resize frame if it exceeds maximum dimensions, maintaining aspect ratio.
    
    Args:
        frame: OpenCV frame (numpy array).
        max_width: Maximum allowed width.
        max_height: Maximum allowed height.
        
    Returns:
        Resized frame (or original if already within limits).
    """
    h, w = frame.shape[:2]

    if w <= max_width and h <= max_height:
        return frame

    # Calculate scale factor to fit within bounds
    scale = min(max_width / w, max_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized


def ensure_directory(path: str) -> str:
    """Create directory if it doesn't exist and return the path."""
    os.makedirs(path, exist_ok=True)
    return path
