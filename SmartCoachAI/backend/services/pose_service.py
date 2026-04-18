"""
SportIQ — Pose Processing Service
Wraps the ML pose estimation module for use by backend API endpoints.
Handles file path management, processing orchestration, and cleanup.
"""

import os
import sys
import logging
import time

# Add project root to path so we can import the ml module
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from ml.pose_estimator import process_video
from backend.config import (
    PROCESSED_DIR,
    MODEL_COMPLEXITY,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    MAX_PROCESS_WIDTH,
    MAX_PROCESS_HEIGHT,
)

logger = logging.getLogger(__name__)


class PoseService:
    """
    Service layer for pose estimation processing.
    Manages the lifecycle of video processing: input validation,
    ML pipeline execution, and output path resolution.
    """

    def __init__(self):
        """Initialize the pose service and ensure output directories exist."""
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        logger.info(f"PoseService initialized. Output dir: {PROCESSED_DIR}")

    def process_cricket_video(self, input_path: str, sport: str = "cricket") -> dict:
        """
        Process an uploaded cricket video through the pose estimation pipeline.
        
        Args:
            input_path: Path to the uploaded video file.
            sport: Sport type (currently only 'cricket' supported).
            
        Returns:
            Dictionary with processing results including output paths and stats.
            
        Raises:
            ValueError: If sport type is unsupported.
            FileNotFoundError: If input video doesn't exist.
        """
        if sport != "cricket":
            raise ValueError(f"Sport '{sport}' is not supported yet. Supported: ['cricket']")

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video not found: {input_path}")

        logger.info(f"Starting pose estimation for: {os.path.basename(input_path)}")
        start_time = time.time()

        try:
            result = process_video(
                input_path=input_path,
                output_dir=PROCESSED_DIR,
                model_complexity=MODEL_COMPLEXITY,
                min_detection_confidence=MIN_DETECTION_CONFIDENCE,
                min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
                draw_skeleton=True,
                extract_keypoints=True,
                max_width=MAX_PROCESS_WIDTH,
                max_height=MAX_PROCESS_HEIGHT,
            )

            # Add output filenames for URL construction
            result["output_video_filename"] = os.path.basename(result["output_video_path"])
            if result["keypoints_json_path"]:
                result["keypoints_filename"] = os.path.basename(result["keypoints_json_path"])
            else:
                result["keypoints_filename"] = None

            result["sport"] = sport
            total_time = round(time.time() - start_time, 2)
            result["total_service_time_seconds"] = total_time

            logger.info(
                f"✅ Pose estimation complete: {result['frames_with_pose']}/{result['total_frames']} "
                f"frames with pose detected ({result['detection_rate']}%) in {total_time}s"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Pose estimation failed: {str(e)}")
            raise

    def cleanup_input(self, input_path: str):
        """Remove the uploaded input file after processing."""
        try:
            if os.path.exists(input_path):
                os.remove(input_path)
                logger.info(f"Cleaned up input file: {input_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup input file: {e}")

    def get_processed_video_path(self, filename: str) -> str:
        """
        Get the full path to a processed video file.
        
        Args:
            filename: Name of the processed video file.
            
        Returns:
            Full path to the file.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        path = os.path.join(PROCESSED_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Processed video not found: {filename}")
        return path

    def get_keypoints_path(self, filename: str) -> str:
        """
        Get the full path to a keypoints JSON file.
        
        Args:
            filename: Name of the keypoints JSON file.
            
        Returns:
            Full path to the file.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
        """
        path = os.path.join(PROCESSED_DIR, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Keypoints file not found: {filename}")
        return path
