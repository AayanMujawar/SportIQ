"""
SportIQ — Pose Estimator (Core Pipeline)
Orchestrates MediaPipe pose estimation on cricket videos.
Draws skeleton overlays and extracts keypoint data.
"""

import cv2
import mediapipe as mp
import os
import time
import logging

from .skeleton_drawer import SkeletonDrawer
from .keypoint_extractor import KeypointExtractor
from .angle_calculator import AngleCalculator
from .utils import get_video_info, create_video_writer, resize_frame, ensure_directory

logger = logging.getLogger(__name__)

# MediaPipe Pose configuration
mp_pose = mp.solutions.pose


def process_video(
    input_path: str,
    output_dir: str,
    model_complexity: int = 1,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
    draw_skeleton: bool = True,
    extract_keypoints: bool = True,
    max_width: int = 1280,
    max_height: int = 720,
) -> dict:
    """
    Process a cricket video with MediaPipe pose estimation.
    
    This is the main entry point for the ML pipeline. It:
      1. Opens the input video
      2. Runs MediaPipe Pose on each frame
      3. Draws skeleton overlay (optional)
      4. Extracts keypoint coordinates to JSON (optional)
      5. Saves the processed output video
    
    Args:
        input_path: Path to the input video file.
        output_dir: Directory for output files (video + JSON).
        model_complexity: MediaPipe model complexity (0=Lite, 1=Full, 2=Heavy).
        min_detection_confidence: Minimum confidence for pose detection.
        min_tracking_confidence: Minimum confidence for pose tracking.
        draw_skeleton: Whether to draw skeleton overlay on output video.
        extract_keypoints: Whether to extract and save keypoints to JSON.
        max_width: Maximum frame width for processing.
        max_height: Maximum frame height for processing.
        
    Returns:
        Dictionary with processing results:
        {
            "output_video_path": str,
            "keypoints_json_path": str | None,
            "total_frames": int,
            "frames_with_pose": int,
            "detection_rate": float,
            "processing_time_seconds": float,
            "video_info": dict,
        }
        
    Raises:
        FileNotFoundError: If input video doesn't exist.
        ValueError: If input video can't be opened.
    """
    start_time = time.time()

    # ── Validate input ────────────────────────────────────────
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")

    video_info = get_video_info(input_path)
    logger.info(f"Processing video: {input_path}")
    logger.info(f"Video: {video_info['width']}x{video_info['height']} @ {video_info['fps']}fps")

    # ── Setup output paths ────────────────────────────────────
    ensure_directory(output_dir)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_video_path = os.path.join(output_dir, f"pose_{base_name}.mp4")
    keypoints_json_path = os.path.join(output_dir, f"keypoints_{base_name}.json") if extract_keypoints else None

    # ── Initialize components ─────────────────────────────────
    skeleton_drawer = SkeletonDrawer(min_visibility=0.5)
    keypoint_extractor = KeypointExtractor(
        video_name=os.path.basename(input_path),
        fps=video_info["fps"],
    )
    angle_calculator = AngleCalculator()

    # ── Open input video ──────────────────────────────────────
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open input video: {input_path}")

    # Read first frame to determine actual output dimensions
    ret, first_frame = cap.read()
    if not ret:
        cap.release()
        raise ValueError(f"Cannot read frames from: {input_path}")

    first_frame = resize_frame(first_frame, max_width, max_height)
    out_h, out_w = first_frame.shape[:2]

    # Reset video to beginning
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    # ── Create output video writer ────────────────────────────
    writer = create_video_writer(
        output_video_path,
        video_info["fps"],
        out_w,
        out_h,
    )

    if not writer.isOpened():
        cap.release()
        raise ValueError(f"Cannot create output video writer for: {output_video_path}")

    # ── Process frames with MediaPipe Pose ────────────────────
    total_frames = 0
    frames_with_pose = 0

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=model_complexity,
        smooth_landmarks=True,
        enable_segmentation=False,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    ) as pose:

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            total_frames += 1
            frame = resize_frame(frame, max_width, max_height)

            # Convert BGR → RGB for MediaPipe (critical for accuracy!)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Run pose estimation
            results = pose.process(frame_rgb)

            # Check if pose was detected
            if results.pose_landmarks:
                frames_with_pose += 1

                # Draw skeleton overlay
                if draw_skeleton:
                    frame = skeleton_drawer.draw(frame, results.pose_landmarks)

                # Extract keypoints
                if extract_keypoints:
                    keypoint_extractor.extract_frame_keypoints(
                        results.pose_landmarks, total_frames - 1
                    )

            # Write frame to output (with or without skeleton)
            writer.write(frame)

            # Progress logging every 100 frames
            if total_frames % 100 == 0:
                logger.info(f"  Processed {total_frames} frames...")

    # ── Cleanup ───────────────────────────────────────────────
    cap.release()
    writer.release()

    # Save keypoints JSON
    if extract_keypoints and keypoints_json_path:
        keypoint_extractor.save_to_json(keypoints_json_path)

    processing_time = round(time.time() - start_time, 2)
    detection_rate = round(frames_with_pose / total_frames * 100, 1) if total_frames > 0 else 0

    result = {
        "output_video_path": output_video_path,
        "keypoints_json_path": keypoints_json_path,
        "total_frames": total_frames,
        "frames_with_pose": frames_with_pose,
        "detection_rate": detection_rate,
        "processing_time_seconds": processing_time,
        "video_info": {
            "original_resolution": f"{video_info['width']}x{video_info['height']}",
            "processed_resolution": f"{out_w}x{out_h}",
            "fps": video_info["fps"],
            "duration_seconds": video_info["duration_seconds"],
        },
    }

    logger.info(
        f"✅ Processing complete: {total_frames} frames, "
        f"{frames_with_pose} with pose ({detection_rate}%), "
        f"took {processing_time}s"
    )

    return result
