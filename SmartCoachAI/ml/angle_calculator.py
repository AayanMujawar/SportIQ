"""
SportIQ — Angle Calculator
Computes joint angles between three keypoints using vector math.
Focused on cricket-specific body angles for shot analysis.
"""

import numpy as np
import logging

logger = logging.getLogger(__name__)


class AngleCalculator:
    """
    Calculates angles between body joints for cricket technique analysis.
    
    Key cricket angles measured:
      - Elbow angle: bat grip and swing mechanics
      - Knee angle: stance depth and balance
      - Shoulder angle: body rotation and weight transfer
      - Hip angle: lower body power generation
    """

    # ── Cricket-Specific Angle Definitions ────────────────────
    # Each angle is defined by three landmark IDs: (point_a, vertex, point_b)
    # The angle is measured at the vertex point.
    CRICKET_ANGLES = {
        "left_elbow": {
            "landmarks": (11, 13, 15),  # left_shoulder → left_elbow → left_wrist
            "description": "Left elbow bend — bat grip angle",
        },
        "right_elbow": {
            "landmarks": (12, 14, 16),  # right_shoulder → right_elbow → right_wrist
            "description": "Right elbow bend — bat control",
        },
        "left_knee": {
            "landmarks": (23, 25, 27),  # left_hip → left_knee → left_ankle
            "description": "Left knee bend — front foot stance",
        },
        "right_knee": {
            "landmarks": (24, 26, 28),  # right_hip → right_knee → right_ankle
            "description": "Right knee bend — back foot stance",
        },
        "left_shoulder": {
            "landmarks": (13, 11, 23),  # left_elbow → left_shoulder → left_hip
            "description": "Left shoulder opening — upper body rotation",
        },
        "right_shoulder": {
            "landmarks": (14, 12, 24),  # right_elbow → right_shoulder → right_hip
            "description": "Right shoulder opening — upper body rotation",
        },
        "left_hip": {
            "landmarks": (11, 23, 25),  # left_shoulder → left_hip → left_knee
            "description": "Left hip angle — weight transfer",
        },
        "right_hip": {
            "landmarks": (12, 24, 26),  # right_shoulder → right_hip → right_knee
            "description": "Right hip angle — weight transfer",
        },
    }

    @staticmethod
    def calculate_angle(point_a: tuple, vertex: tuple, point_b: tuple) -> float:
        """
        Calculate the angle at the vertex point formed by three 2D points.
        
        Uses the dot product formula:
            angle = arccos( (VA · VB) / (|VA| × |VB|) )
        
        Args:
            point_a: (x, y) coordinates of the first point.
            vertex: (x, y) coordinates of the vertex (where angle is measured).
            point_b: (x, y) coordinates of the third point.
            
        Returns:
            Angle in degrees (0–180).
        """
        a = np.array(point_a)
        v = np.array(vertex)
        b = np.array(point_b)

        # Vectors from vertex to each point
        va = a - v
        vb = b - v

        # Calculate angle using dot product
        cos_angle = np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-8)

        # Clamp to valid range to avoid numerical errors with arccos
        cos_angle = np.clip(cos_angle, -1.0, 1.0)

        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)

        return round(float(angle_deg), 2)

    def calculate_cricket_angles(self, landmarks) -> dict:
        """
        Calculate all cricket-specific joint angles from pose landmarks.
        
        Args:
            landmarks: MediaPipe pose landmarks for one frame.
            
        Returns:
            Dictionary mapping angle names to their values and metadata.
            Example: {
                "left_elbow": {
                    "angle_degrees": 145.5,
                    "description": "Left elbow bend — bat grip angle"
                },
                ...
            }
        """
        if landmarks is None:
            return {}

        results = {}
        landmark_list = landmarks.landmark

        for angle_name, angle_def in self.CRICKET_ANGLES.items():
            idx_a, idx_v, idx_b = angle_def["landmarks"]

            lm_a = landmark_list[idx_a]
            lm_v = landmark_list[idx_v]
            lm_b = landmark_list[idx_b]

            # Check visibility of all three landmarks
            min_vis = min(lm_a.visibility, lm_v.visibility, lm_b.visibility)

            if min_vis < 0.3:
                results[angle_name] = {
                    "angle_degrees": None,
                    "visibility": round(min_vis, 3),
                    "description": angle_def["description"],
                    "status": "low_visibility",
                }
                continue

            angle = self.calculate_angle(
                (lm_a.x, lm_a.y),
                (lm_v.x, lm_v.y),
                (lm_b.x, lm_b.y),
            )

            results[angle_name] = {
                "angle_degrees": angle,
                "visibility": round(min_vis, 3),
                "description": angle_def["description"],
                "status": "ok",
            }

        return results

    def get_frame_summary(self, landmarks) -> dict:
        """
        Get a simplified angle summary for a frame (just angle values).
        Used for quick comparisons and scoring.
        
        Returns:
            Dictionary of {angle_name: angle_value} pairs.
        """
        angles = self.calculate_cricket_angles(landmarks)
        return {
            name: data["angle_degrees"]
            for name, data in angles.items()
            if data["angle_degrees"] is not None
        }
