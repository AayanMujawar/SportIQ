"""
SportIQ — Shot Classifier
Rule-based cricket shot type classification using joint angle signatures.
Analyzes the min/max angle ranges across a video to identify the most likely shot.
"""

import logging

logger = logging.getLogger(__name__)


class ShotClassifier:
    """
    Classifies cricket shot types based on joint angle patterns.
    
    Uses heuristic rules derived from biomechanical analysis of common
    cricket shots. Each shot has a characteristic "signature" of joint
    angle ranges that distinguish it from other shot types.
    """

    # ── Shot Angle Signatures ────────────────────────────────────
    # Each shot type has expected angle ranges for key joints.
    # Format: { joint_name: (expected_min, expected_max) }
    # These are approximate — real-world values vary by player.
    SHOT_SIGNATURES = {
        "cover_drive": {
            "description": "Cover Drive",
            "icon": "🏏",
            "left_elbow":     (140, 180),
            "right_elbow":    (90, 170),
            "left_knee":      (120, 170),
            "right_knee":     (150, 178),
            "left_shoulder":  (30, 90),
            "right_shoulder": (20, 100),
            "left_hip":       (110, 170),
            "right_hip":      (140, 175),
        },
        "straight_drive": {
            "description": "Straight Drive",
            "icon": "🏏",
            "left_elbow":     (150, 180),
            "right_elbow":    (80, 165),
            "left_knee":      (130, 175),
            "right_knee":     (150, 178),
            "left_shoulder":  (25, 80),
            "right_shoulder": (25, 110),
            "left_hip":       (120, 170),
            "right_hip":      (140, 178),
        },
        "pull_shot": {
            "description": "Pull Shot",
            "icon": "💪",
            "left_elbow":     (100, 170),
            "right_elbow":    (60, 150),
            "left_knee":      (100, 160),
            "right_knee":     (120, 170),
            "left_shoulder":  (40, 120),
            "right_shoulder": (30, 130),
            "left_hip":       (90, 160),
            "right_hip":      (110, 170),
        },
        "cut_shot": {
            "description": "Cut Shot",
            "icon": "⚔️",
            "left_elbow":     (120, 175),
            "right_elbow":    (70, 155),
            "left_knee":      (110, 165),
            "right_knee":     (130, 175),
            "left_shoulder":  (35, 100),
            "right_shoulder": (40, 130),
            "left_hip":       (100, 165),
            "right_hip":      (120, 170),
        },
        "sweep_shot": {
            "description": "Sweep Shot",
            "icon": "🧹",
            "left_elbow":     (110, 170),
            "right_elbow":    (60, 150),
            "left_knee":      (40, 120),   # Deep knee bend is signature
            "right_knee":     (90, 160),
            "left_shoulder":  (30, 110),
            "right_shoulder": (20, 100),
            "left_hip":       (60, 140),   # Low hip position
            "right_hip":      (80, 160),
        },
        "defensive_block": {
            "description": "Defensive Block",
            "icon": "🛡️",
            "left_elbow":     (150, 180),  # Straighter arms
            "right_elbow":    (130, 180),
            "left_knee":      (130, 175),
            "right_knee":     (140, 178),
            "left_shoulder":  (15, 60),    # Compact shoulder position
            "right_shoulder": (15, 60),
            "left_hip":       (140, 178),  # Upright stance
            "right_hip":      (150, 178),
        },
        "lofted_shot": {
            "description": "Lofted Shot",
            "icon": "🚀",
            "left_elbow":     (120, 175),
            "right_elbow":    (50, 140),
            "left_knee":      (100, 165),
            "right_knee":     (110, 170),
            "left_shoulder":  (50, 140),   # High shoulder lift
            "right_shoulder": (40, 140),
            "left_hip":       (80, 160),
            "right_hip":      (100, 165),
        },
        "flick_shot": {
            "description": "Flick Shot",
            "icon": "✋",
            "left_elbow":     (120, 175),
            "right_elbow":    (70, 160),
            "left_knee":      (110, 165),
            "right_knee":     (120, 170),
            "left_shoulder":  (25, 90),
            "right_shoulder": (30, 110),
            "left_hip":       (100, 165),
            "right_hip":      (120, 170),
        },
    }

    def classify_shot(self, user_ranges: dict, user_selected: str = "other") -> dict:
        """
        Classify the shot type based on user angle ranges.
        
        Priority:
          1. If user explicitly selected a shot type → always use it
          2. If user chose "Auto Detect" (other) → run angle-based classification
        
        Args:
            user_ranges: Dictionary of { joint_name: { "min": float, "max": float } }
            user_selected: The shot type selected by the user (from dropdown).
            
        Returns:
            Dictionary with detected_shot, display_name, icon, confidence, method, all_scores.
        """
        # Always compute match scores for reference (shown in report)
        scores = {}
        if user_ranges:
            for shot_name, signature in self.SHOT_SIGNATURES.items():
                score = self._calculate_match_score(user_ranges, signature)
                scores[shot_name] = round(score, 3)

        # ── Priority 1: User explicitly selected a shot ───────────
        if user_selected != "other" and user_selected in self.SHOT_SIGNATURES:
            sig = self.SHOT_SIGNATURES[user_selected]
            return {
                "detected_shot": user_selected,
                "display_name": sig["description"],
                "icon": sig["icon"],
                "confidence": 1.0,
                "method": "user_selected",
                "all_scores": scores,
            }

        # ── Priority 2: Auto-detect from angle patterns ───────────
        if not user_ranges or not scores:
            return self._user_fallback(user_selected)

        best_shot = max(scores, key=scores.get)
        best_score = scores[best_shot]
        sig = self.SHOT_SIGNATURES[best_shot]
        
        return {
            "detected_shot": best_shot,
            "display_name": sig["description"],
            "icon": sig["icon"],
            "confidence": round(best_score, 3),
            "method": "auto_detected",
            "all_scores": scores,
        }

    def _calculate_match_score(self, user_ranges: dict, signature: dict) -> float:
        """
        Calculate how well user angle ranges match a shot signature.
        Returns a score between 0.0 (no match) and 1.0 (perfect match).
        """
        total_score = 0.0
        total_joints = 0

        for joint_name in ["left_elbow", "right_elbow", "left_knee", "right_knee",
                           "left_shoulder", "right_shoulder", "left_hip", "right_hip"]:
            if joint_name not in user_ranges or joint_name not in signature:
                continue

            user_min = user_ranges[joint_name].get("min")
            user_max = user_ranges[joint_name].get("max")
            
            if user_min is None or user_max is None:
                continue

            expected_min, expected_max = signature[joint_name]

            # Score based on how close user range is to expected range
            min_diff = abs(user_min - expected_min)
            max_diff = abs(user_max - expected_max)
            
            # Normalize: 0 diff = 1.0 score, 60+ diff = 0.0 score
            MAX_DEVIATION = 60.0
            min_score = max(0, 1.0 - (min_diff / MAX_DEVIATION))
            max_score = max(0, 1.0 - (max_diff / MAX_DEVIATION))
            
            joint_score = (min_score + max_score) / 2.0
            total_score += joint_score
            total_joints += 1

        return total_score / total_joints if total_joints > 0 else 0.0

    def _user_fallback(self, user_selected: str) -> dict:
        """Return result based on user's dropdown selection."""
        if user_selected in self.SHOT_SIGNATURES:
            sig = self.SHOT_SIGNATURES[user_selected]
            return {
                "detected_shot": user_selected,
                "display_name": sig["description"],
                "icon": sig["icon"],
                "confidence": 1.0,
                "method": "user_selected",
                "all_scores": {},
            }
        
        return {
            "detected_shot": "other",
            "display_name": "Cricket Shot",
            "icon": "🏏",
            "confidence": 0.0,
            "method": "unknown",
            "all_scores": {},
        }
