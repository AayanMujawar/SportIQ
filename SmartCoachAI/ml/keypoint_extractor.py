"""
SportIQ — Keypoint Extractor
Extracts pose landmark coordinates from MediaPipe results
and serializes them to structured JSON for analysis.
"""

import json
import os
import logging
import mediapipe as mp

logger = logging.getLogger(__name__)

mp_pose = mp.solutions.pose

# Human-readable landmark names (all 33 MediaPipe pose landmarks)
LANDMARK_NAMES = [
    "nose",
    "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear",
    "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow",
    "left_wrist", "right_wrist",
    "left_pinky", "right_pinky",
    "left_index", "right_index",
    "left_thumb", "right_thumb",
    "left_hip", "right_hip",
    "left_knee", "right_knee",
    "left_ankle", "right_ankle",
    "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]


class KeypointExtractor:
    """
    Extracts and stores pose keypoints from MediaPipe pose estimation results.
    Supports frame-by-frame accumulation and JSON export.
    """

    def __init__(self, video_name: str = "", fps: float = 30.0):
        """
        Args:
            video_name: Name of the source video (stored in JSON metadata).
            fps: Video frames per second (stored in JSON metadata).
        """
        self.video_name = video_name
        self.fps = fps
        self.frames_data = []

    def extract_frame_keypoints(self, landmarks, frame_number: int) -> dict:
        """
        Extract keypoint data from a single frame's pose landmarks.
        
        Args:
            landmarks: MediaPipe pose landmarks for one frame.
            frame_number: The frame index (0-based).
            
        Returns:
            Dictionary containing frame number and list of landmark data.
            Returns None if no landmarks detected.
        """
        if landmarks is None:
            return None

        frame_data = {
            "frame_number": frame_number,
            "timestamp_seconds": round(frame_number / self.fps, 4) if self.fps > 0 else 0,
            "landmarks": [],
        }

        for idx, lm in enumerate(landmarks.landmark):
            landmark_data = {
                "id": idx,
                "name": LANDMARK_NAMES[idx] if idx < len(LANDMARK_NAMES) else f"landmark_{idx}",
                "x": round(lm.x, 6),
                "y": round(lm.y, 6),
                "z": round(lm.z, 6),
                "visibility": round(lm.visibility, 4),
            }
            frame_data["landmarks"].append(landmark_data)

        self.frames_data.append(frame_data)
        return frame_data

    def get_all_keypoints(self) -> dict:
        """
        Get the complete keypoints data structure.
        
        Returns:
            Dictionary with video metadata and all frame keypoints.
        """
        return {
            "video_name": self.video_name,
            "fps": self.fps,
            "total_frames_processed": len(self.frames_data),
            "landmark_count": 33,
            "landmark_names": LANDMARK_NAMES,
            "frames": self.frames_data,
        }

    def save_to_json(self, output_path: str) -> str:
        """
        Save all extracted keypoints to a JSON file.
        
        Args:
            output_path: Path for the output JSON file.
            
        Returns:
            The output file path.
        """
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        data = self.get_all_keypoints()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Keypoints saved: {len(self.frames_data)} frames → {output_path}"
        )
        return output_path

    def get_landmark_trajectory(self, landmark_id: int) -> list:
        """
        Get the (x, y) trajectory of a specific landmark across all frames.
        Useful for analyzing movement patterns (e.g., wrist path during a shot).
        
        Args:
            landmark_id: MediaPipe landmark index (0-32).
            
        Returns:
            List of (frame_number, x, y, visibility) tuples.
        """
        trajectory = []
        for frame in self.frames_data:
            for lm in frame["landmarks"]:
                if lm["id"] == landmark_id:
                    trajectory.append({
                        "frame": frame["frame_number"],
                        "x": lm["x"],
                        "y": lm["y"],
                        "visibility": lm["visibility"],
                    })
                    break
        return trajectory
