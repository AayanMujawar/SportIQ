import json
import os

# Default mock ideal angles if the user hasn't generated their own yet
# Values represent typical range of motion (min/max degrees)
IDEAL_MOCK = {
    "left_elbow": {"min": 150.0, "max": 180.0},
    "right_elbow": {"min": 60.0, "max": 160.0},
    "left_knee": {"min": 110.0, "max": 170.0},
    "right_knee": {"min": 140.0, "max": 178.0},
    "left_shoulder": {"min": 20.0, "max": 90.0},
    "right_shoulder": {"min": 20.0, "max": 120.0},
    "left_hip": {"min": 100.0, "max": 170.0},
    "right_hip": {"min": 130.0, "max": 175.0}
}

if __name__ == "__main__":
    with open(os.path.join(os.path.dirname(__file__), "ideal_angles.json"), "w") as f:
        json.dump(IDEAL_MOCK, f, indent=4)
