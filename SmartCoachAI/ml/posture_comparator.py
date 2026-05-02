"""
SportIQ — Posture Comparator
Calculates the posture error rate by comparing a user's joint angle 
extremes (min/max) against an ideal reference.

Enhanced for 50% project: returns per-joint breakdowns, coaching tips,
and performance grades.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)


# ── Coaching Tip Templates ───────────────────────────────────────
# Tips keyed by joint name, with suggestions for common deviations.
COACHING_TIPS = {
    "left_elbow": {
        "high_error": "Your front arm isn't extending fully. Focus on straightening your left elbow through the shot for better bat control. Injury Prevention: Avoid snapping the elbow joint quickly to prevent hyperextension.",
        "medium_error": "Your left elbow extension is decent but could be straighter at the point of contact. Ensure smooth movement to protect the joint.",
        "low_error": "Good left elbow positioning! Your front arm extension is close to ideal, minimizing stress on the elbow tendons.",
        "icon": "💪",
        "joint_label": "Left Elbow",
    },
    "right_elbow": {
        "high_error": "Your bottom hand grip is too tight or loose. Work on keeping your right elbow at a controlled angle. Injury Prevention: A relaxed grip prevents tennis elbow and wrist strain.",
        "medium_error": "Right elbow angle is slightly off. Practice shadow batting to build muscle memory without overstraining.",
        "low_error": "Solid right elbow mechanics. Your bottom hand control is well-managed, preventing unnecessary ligament tension.",
        "icon": "💪",
        "joint_label": "Right Elbow",
    },
    "left_knee": {
        "high_error": "Your front knee is not bending enough for a stable stance. Get lower to the pitch. Injury Prevention: A stiff front knee absorbs too much impact; bending it protects the meniscus and ligaments.",
        "medium_error": "Front knee bend is close but could be deeper. A lower center of gravity improves balance and distributes weight safely.",
        "low_error": "Excellent front knee positioning! Your stance depth matches professional form, providing a safe shock-absorbing base.",
        "icon": "🦵",
        "joint_label": "Left Knee",
    },
    "right_knee": {
        "high_error": "Your back knee positioning needs work. Focus on keeping it stable and slightly bent. Injury Prevention: Avoid locking the back knee to prevent ACL/PCL injuries during weight transfer.",
        "medium_error": "Back knee angle is slightly off. Practice shifting weight smoothly to avoid sudden twisting of the knee joint.",
        "low_error": "Great back knee stability. Your lower body foundation is strong and biomechanically safe.",
        "icon": "🦵",
        "joint_label": "Right Knee",
    },
    "left_shoulder": {
        "high_error": "Your shoulder rotation is limited. Open up your front shoulder more. Injury Prevention: Forcing the arms without shoulder rotation places excessive strain on the rotator cuff.",
        "medium_error": "Shoulder opening is close to ideal. Focus on leading with your front shoulder safely during the downswing.",
        "low_error": "Excellent shoulder rotation! Your upper body mechanics are fluid, reducing the risk of impingement.",
        "icon": "🔄",
        "joint_label": "Left Shoulder",
    },
    "right_shoulder": {
        "high_error": "Your trailing shoulder isn't rotating enough. Work on full follow-through. Injury Prevention: A restricted follow-through forces the shoulder to decelerate too quickly, risking muscle tears.",
        "medium_error": "Right shoulder rotation is almost there. Focus on completing the full arc to decelerate the bat smoothly.",
        "low_error": "Strong right shoulder mechanics. Your follow-through safely dissipates the swing's energy.",
        "icon": "🔄",
        "joint_label": "Right Shoulder",
    },
    "left_hip": {
        "high_error": "Your hip alignment is off. Practice transferring weight by driving your front hip toward the ball. Injury Prevention: Proper hip alignment protects the lower back from absorbing torsional stress.",
        "medium_error": "Hip positioning is close. A slight adjustment will improve power transfer and reduce lumbar strain.",
        "low_error": "Good hip alignment! Your lower body power generation protects your spine effectively.",
        "icon": "🏃",
        "joint_label": "Left Hip",
    },
    "right_hip": {
        "high_error": "Your back hip isn't opening up enough. Focus on rotating your hips. Injury Prevention: Limited hip rotation forces the lower back to over-rotate, which is a leading cause of back spasms.",
        "medium_error": "Right hip rotation is slightly restricted. Work on hip mobility drills to ensure safe rotation.",
        "low_error": "Excellent hip rotation! Your weight transfer is well-executed and biomechanically sound.",
        "icon": "🏃",
        "joint_label": "Right Hip",
    },
}


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

    def calculate_detailed_analysis(self, user_ranges: dict) -> dict:
        """
        Enhanced analysis returning per-joint breakdowns, coaching tips, and grade.
        
        Args:
            user_ranges: { joint_name: { "min": float, "max": float } }
            
        Returns:
            {
                "overall_error_rate": float,
                "overall_score": float,        # 100 - error_rate
                "performance_grade": str,       # "A+", "A", "B+", etc.
                "joint_details": [...],         # per-joint breakdown
                "coaching_tips": [...],         # improvement suggestions
            }
        """
        overall_error = self.calculate_error_rate(user_ranges)
        overall_score = round(100.0 - overall_error, 1)
        grade = self._calculate_grade(overall_score)
        
        joint_details = self._get_joint_details(user_ranges)
        coaching_tips = self._generate_coaching_tips(joint_details)
        
        return {
            "overall_error_rate": overall_error,
            "overall_score": overall_score,
            "performance_grade": grade,
            "joint_details": joint_details,
            "coaching_tips": coaching_tips,
        }

    def _get_joint_details(self, user_ranges: dict) -> list:
        """Calculate per-joint error details."""
        details = []
        
        TOLERANCE_DEGREES = 10.0
        PENALTY_CAP = 45.0
        
        for joint, ideal_range in self.ideal_data.items():
            if joint not in user_ranges:
                continue
                
            user_min = user_ranges[joint].get("min")
            user_max = user_ranges[joint].get("max")
            ideal_min = ideal_range.get("min")
            ideal_max = ideal_range.get("max")
            
            if None in (user_min, user_max, ideal_min, ideal_max):
                continue
            
            max_diff = max(0, abs(user_max - ideal_max) - TOLERANCE_DEGREES)
            min_diff = max(0, abs(user_min - ideal_min) - TOLERANCE_DEGREES)
            
            penalty = min(PENALTY_CAP, max_diff) + min(PENALTY_CAP, min_diff)
            max_possible = PENALTY_CAP * 2
            
            joint_error = round((penalty / max_possible) * 100, 1) if max_possible > 0 else 0
            joint_score = round(100 - joint_error, 1)
            
            # Determine status
            if joint_score >= 85:
                status = "excellent"
            elif joint_score >= 65:
                status = "good"
            elif joint_score >= 40:
                status = "needs_work"
            else:
                status = "poor"
            
            tip_data = COACHING_TIPS.get(joint, {})
            
            details.append({
                "joint_name": joint,
                "joint_label": tip_data.get("joint_label", joint.replace("_", " ").title()),
                "icon": tip_data.get("icon", "📐"),
                "user_min": round(user_min, 1),
                "user_max": round(user_max, 1),
                "ideal_min": round(ideal_min, 1),
                "ideal_max": round(ideal_max, 1),
                "error_percent": joint_error,
                "score_percent": joint_score,
                "status": status,
            })
        
        # Sort by error (worst joints first)
        details.sort(key=lambda x: x["error_percent"], reverse=True)
        
        return details

    def _generate_coaching_tips(self, joint_details: list) -> list:
        """Generate coaching tips based on joint deviations."""
        tips = []
        
        for detail in joint_details:
            joint_name = detail["joint_name"]
            error = detail["error_percent"]
            
            tip_data = COACHING_TIPS.get(joint_name)
            if not tip_data:
                continue
            
            if error >= 40:
                tip_text = tip_data["high_error"]
                severity = "high"
            elif error >= 15:
                tip_text = tip_data["medium_error"]
                severity = "medium"
            else:
                tip_text = tip_data["low_error"]
                severity = "low"
            
            tips.append({
                "joint_name": joint_name,
                "joint_label": tip_data["joint_label"],
                "icon": tip_data["icon"],
                "tip": tip_text,
                "severity": severity,
                "error_percent": error,
            })
        
        # Sort: high severity first, then medium, then low
        severity_order = {"high": 0, "medium": 1, "low": 2}
        tips.sort(key=lambda t: severity_order.get(t["severity"], 3))
        
        return tips

    @staticmethod
    def _calculate_grade(score: float) -> str:
        """Convert a 0-100 score to a letter grade."""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 55:
            return "C-"
        elif score >= 50:
            return "D+"
        elif score >= 45:
            return "D"
        elif score >= 40:
            return "D-"
        else:
            return "F"
