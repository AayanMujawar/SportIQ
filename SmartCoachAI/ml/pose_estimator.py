"""
SportIQ — Pose Estimator (Core Pipeline)
Orchestrates MediaPipe pose estimation on cricket videos.
Draws skeleton overlays and extracts keypoint data.

Enhanced for 50% project: integrates shot classification,
collects per-frame angle timelines, and returns detailed analysis.
"""

import cv2
import mediapipe as mp
import os
import time
import logging

from .skeleton_drawer import SkeletonDrawer
from .keypoint_extractor import KeypointExtractor
from .angle_calculator import AngleCalculator
from .posture_comparator import PostureComparator
from .shot_classifier import ShotClassifier
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
    shot_type: str = "other",
) -> dict:
    """
    Process a cricket video with MediaPipe pose estimation.
    
    This is the main entry point for the ML pipeline. It:
      1. Opens the input video
      2. Runs MediaPipe Pose on each frame
      3. Draws skeleton overlay (optional)
      4. Extracts keypoint coordinates to JSON (optional)
      5. Classifies the shot type from angle patterns
      6. Generates detailed posture analysis with per-joint breakdown
      7. Collects angle timeline for visualization
      8. Saves the processed output video
    
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
        shot_type: User-selected shot type (used as fallback for classifier).
        
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
            "posture_error_rate": float,
            "detailed_analysis": dict,
            "shot_classification": dict,
            "angle_timeline": dict,
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
    posture_comparator = PostureComparator()
    shot_classifier = ShotClassifier()
    
    # Store user angle ranges
    user_ranges = {k: {"min": float('inf'), "max": float('-inf')} for k in angle_calculator.CRICKET_ANGLES.keys()}
    
    # ── Angle timeline data (sampled) ─────────────────────────
    # Store per-frame angles for key joints (sampled to reduce data size)
    angle_timeline = {k: [] for k in angle_calculator.CRICKET_ANGLES.keys()}
    SAMPLE_INTERVAL = max(1, int(video_info["fps"] / 5))  # ~5 samples per second

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
                    
                # Calculate angles for this frame
                angles = angle_calculator.calculate_cricket_angles(results.pose_landmarks)
                
                for angle_name, angle_data in angles.items():
                    val = angle_data.get("angle_degrees")
                    if val is not None and angle_data.get("status") == "ok":
                        # Track user Min/Max angles
                        if val < user_ranges[angle_name]["min"]:
                            user_ranges[angle_name]["min"] = val
                        if val > user_ranges[angle_name]["max"]:
                            user_ranges[angle_name]["max"] = val
                        
                        # Collect timeline samples
                        if (total_frames - 1) % SAMPLE_INTERVAL == 0:
                            angle_timeline[angle_name].append({
                                "frame": total_frames - 1,
                                "value": round(val, 1),
                            })

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

    # Clean up unrecorded user max limits
    final_user_ranges = {}
    for k, v in user_ranges.items():
        if v["min"] != float('inf') and v["max"] != float('-inf'):
            final_user_ranges[k] = v

    # ── Calculate detailed posture analysis ───────────────────
    detailed_analysis = posture_comparator.calculate_detailed_analysis(final_user_ranges)
    posture_error_rate = detailed_analysis["overall_error_rate"]
    
    # ── Classify shot type ────────────────────────────────────
    shot_classification = shot_classifier.classify_shot(final_user_ranges, shot_type)
    
    # ── Clean up timeline (remove empty joints) ──────────────
    clean_timeline = {}
    for joint_name, data_points in angle_timeline.items():
        if data_points:
            clean_timeline[joint_name] = data_points

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
        "posture_error_rate": posture_error_rate,
        "detailed_analysis": detailed_analysis,
        "shot_classification": shot_classification,
        "angle_timeline": clean_timeline,
    }

    logger.info(
        f"✅ Processing complete: {total_frames} frames, "
        f"{frames_with_pose} with pose ({detection_rate}%), "
        f"shot: {shot_classification['display_name']}, "
        f"grade: {detailed_analysis['performance_grade']}, "
        f"took {processing_time}s"
    )

    return result
