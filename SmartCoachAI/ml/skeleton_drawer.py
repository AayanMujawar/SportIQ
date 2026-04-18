"""
SportIQ — Skeleton Drawer
Draws pose landmarks and connecting bones on video frames using 
a cricket-specific color scheme for visual analysis.
"""

import cv2
import mediapipe as mp
import numpy as np
import logging

logger = logging.getLogger(__name__)

# MediaPipe pose landmark indices
mp_pose = mp.solutions.pose


class SkeletonDrawer:
    """
    Draws MediaPipe pose landmarks and skeleton connections on video frames.
    
    Uses a cricket-specific color scheme:
      - Neon Green (#00FF88) — Upper body (bat swing analysis)
      - Cyan (#00E5FF) — Torso (hip alignment & rotation)
      - Orange (#FF6D00) — Lower body (footwork & stance)
      - White — Face landmarks
    """

    # ── Color Definitions (BGR format for OpenCV) ─────────────
    COLOR_UPPER = (0x88, 0xFF, 0x00)     # Neon green (BGR) — shoulders, elbows, wrists
    COLOR_TORSO = (0xFF, 0xE5, 0x00)     # Cyan (BGR) — spine, hips
    COLOR_LOWER = (0x00, 0x6D, 0xFF)     # Orange (BGR) — knees, ankles, feet
    COLOR_FACE = (0xFF, 0xFF, 0xFF)      # White — nose, eyes, ears
    COLOR_LANDMARK = (0xAA, 0xFF, 0x00)  # Bright green for landmark dots

    # ── Landmark Groups ───────────────────────────────────────
    # Face landmarks (0-10)
    FACE_LANDMARKS = set(range(0, 11))

    # Upper body landmarks
    UPPER_LANDMARKS = {
        mp_pose.PoseLandmark.LEFT_SHOULDER.value,
        mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
        mp_pose.PoseLandmark.LEFT_ELBOW.value,
        mp_pose.PoseLandmark.RIGHT_ELBOW.value,
        mp_pose.PoseLandmark.LEFT_WRIST.value,
        mp_pose.PoseLandmark.RIGHT_WRIST.value,
        mp_pose.PoseLandmark.LEFT_PINKY.value,
        mp_pose.PoseLandmark.RIGHT_PINKY.value,
        mp_pose.PoseLandmark.LEFT_INDEX.value,
        mp_pose.PoseLandmark.RIGHT_INDEX.value,
        mp_pose.PoseLandmark.LEFT_THUMB.value,
        mp_pose.PoseLandmark.RIGHT_THUMB.value,
    }

    # Torso landmarks
    TORSO_LANDMARKS = {
        mp_pose.PoseLandmark.LEFT_SHOULDER.value,
        mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
        mp_pose.PoseLandmark.LEFT_HIP.value,
        mp_pose.PoseLandmark.RIGHT_HIP.value,
    }

    # Lower body landmarks
    LOWER_LANDMARKS = {
        mp_pose.PoseLandmark.LEFT_HIP.value,
        mp_pose.PoseLandmark.RIGHT_HIP.value,
        mp_pose.PoseLandmark.LEFT_KNEE.value,
        mp_pose.PoseLandmark.RIGHT_KNEE.value,
        mp_pose.PoseLandmark.LEFT_ANKLE.value,
        mp_pose.PoseLandmark.RIGHT_ANKLE.value,
        mp_pose.PoseLandmark.LEFT_HEEL.value,
        mp_pose.PoseLandmark.RIGHT_HEEL.value,
        mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value,
        mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value,
    }

    def __init__(self, min_visibility: float = 0.5):
        """
        Args:
            min_visibility: Minimum visibility threshold for drawing landmarks.
                           Landmarks below this threshold are skipped.
        """
        self.min_visibility = min_visibility

    def _get_connection_color(self, start_idx: int, end_idx: int):
        """Determine the color for a bone connection based on landmark groups."""
        if start_idx in self.FACE_LANDMARKS or end_idx in self.FACE_LANDMARKS:
            return self.COLOR_FACE
        if start_idx in self.LOWER_LANDMARKS and end_idx in self.LOWER_LANDMARKS:
            return self.COLOR_LOWER
        if start_idx in self.TORSO_LANDMARKS and end_idx in self.TORSO_LANDMARKS:
            return self.COLOR_TORSO
        return self.COLOR_UPPER

    def _get_landmark_color(self, idx: int):
        """Determine the color for a landmark dot based on its group."""
        if idx in self.FACE_LANDMARKS:
            return self.COLOR_FACE
        if idx in self.LOWER_LANDMARKS:
            return self.COLOR_LOWER
        if idx in self.TORSO_LANDMARKS:
            return self.COLOR_TORSO
        return self.COLOR_UPPER

    def _scale_thickness(self, frame_width: int) -> tuple:
        """Scale line thickness and circle radius based on frame resolution."""
        # Base: 2px line, 4px circle for 640px width
        scale = max(frame_width / 640.0, 0.5)
        line_thickness = max(int(2 * scale), 1)
        circle_radius = max(int(4 * scale), 2)
        return line_thickness, circle_radius

    def draw(self, frame, landmarks) -> np.ndarray:
        """
        Draw pose skeleton on a single frame.
        
        Args:
            frame: OpenCV frame (BGR numpy array).
            landmarks: MediaPipe pose landmarks result.
            
        Returns:
            Frame with skeleton overlay drawn.
        """
        if landmarks is None:
            return frame

        h, w, _ = frame.shape
        line_thickness, circle_radius = self._scale_thickness(w)

        # Create a semi-transparent overlay for a cleaner look
        overlay = frame.copy()

        landmark_list = landmarks.landmark

        # ── Draw connections (bones) first ────────────────────
        for connection in mp_pose.POSE_CONNECTIONS:
            start_idx, end_idx = connection
            start_lm = landmark_list[start_idx]
            end_lm = landmark_list[end_idx]

            # Skip if either landmark has low visibility
            if (start_lm.visibility < self.min_visibility or
                    end_lm.visibility < self.min_visibility):
                continue

            start_point = (int(start_lm.x * w), int(start_lm.y * h))
            end_point = (int(end_lm.x * w), int(end_lm.y * h))
            color = self._get_connection_color(start_idx, end_idx)

            cv2.line(overlay, start_point, end_point, color, line_thickness, cv2.LINE_AA)

        # ── Draw landmark dots on top ─────────────────────────
        for idx, lm in enumerate(landmark_list):
            if lm.visibility < self.min_visibility:
                continue

            cx, cy = int(lm.x * w), int(lm.y * h)
            color = self._get_landmark_color(idx)

            # Outer glow effect
            cv2.circle(overlay, (cx, cy), circle_radius + 2, (0, 0, 0), -1, cv2.LINE_AA)
            # Inner colored dot
            cv2.circle(overlay, (cx, cy), circle_radius, color, -1, cv2.LINE_AA)

        # Blend overlay with original frame (85% opacity for skeleton)
        alpha = 0.85
        result = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        return result
