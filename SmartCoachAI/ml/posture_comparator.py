"""
SportIQ — Posture Comparator
Calculates the posture error rate by comparing a user's joint angle 
extremes (min/max) against an ideal reference.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

class PostureComparator:
    def __init__(self, ideal_json_path: str = None):
        if ideal_json_path is None:
            ideal_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ideal_angles.json")
        
        self.ideal_data = {}
        if os.path.exists(ideal_json_path):
            try:
                with open(ideal_json_path, 'r') as f:
                    self.ideal_data = json.load(f)
                logger.info(f"Loaded ideal angles from {ideal_json_path}")
            except Exception as e:
                logger.error(f"Failed to load ideal angles: {e}")
        else:
            logger.warning(f"Ideal angles JSON not found at {ideal_json_path}. Will use dynamic fallbacks or return 0 error.")

    def calculate_error_rate(self, user_ranges: dict) -> float:
        """
        user_ranges format:
        {
            "left_elbow": {"min": 150.5, "max": 175.2},
            ...
        }
        Returns:
            Error percentage (0.0 to 100.0). 0 means perfect form, 100 means terrible form.
        """
        if not self.ideal_data or not user_ranges:
            return 0.0

        total_penalty = 0.0
        max_possible_penalty = 0.0
        
        # Max deviation allowed before score drops to zero for that joint
        TOLERANCE_DEGREES = 10.0  # Buffer allowed (if you miss the max by 5 degrees, it's ok)
        PENALTY_CAP = 45.0  # If you are 45+ degrees off, max penalty for that joint
        
        for joint, ideal_range in self.ideal_data.items():
            if joint not in user_ranges:
                continue

            user_min = user_ranges[joint].get("min")
            user_max = user_ranges[joint].get("max")
            ideal_min = ideal_range.get("min")
            ideal_max = ideal_range.get("max")

            if None in (user_min, user_max, ideal_min, ideal_max):
                continue
                
            # Feature 1: Check maximum extension difference
            max_diff = max(0, abs(user_max - ideal_max) - TOLERANCE_DEGREES)
            
            # Feature 2: Check maximum bend/flex difference
            min_diff = max(0, abs(user_min - ideal_min) - TOLERANCE_DEGREES)
            
            # Penalty calculation (cap at PENALTY_CAP)
            penalty = min(PENALTY_CAP, max_diff) + min(PENALTY_CAP, min_diff)
            
            total_penalty += penalty
            max_possible_penalty += (PENALTY_CAP * 2)
            
        if max_possible_penalty == 0:
            return 0.0
            
        error_rate = (total_penalty / max_possible_penalty) * 100
        return round(min(100.0, error_rate), 1)
