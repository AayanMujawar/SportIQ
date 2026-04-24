"""
SportIQ — Ideal Angle Extractor
Utility script to process an ideal professional video and extract the 
min and max joint angles, saving them to ideal_angles.json.

Usage:
    python extract_ideal_angles.py <path_to_video.mp4>
"""

import sys
import os
import cv2
import json
import mediapipe as mp
import time

# Ensure we can import from ml
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from ml.angle_calculator import AngleCalculator

def extract_ideal(video_path: str, output_json: str = "ideal_angles.json"):
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)
        
    print(f"Processing ideal video: {video_path}")
    
    mp_pose = mp.solutions.pose
    angle_calculator = AngleCalculator()
    
    cap = cv2.VideoCapture(video_path)
    
    # Store ranges for min/max
    ranges = {}
    for angle_name in angle_calculator.CRICKET_ANGLES.keys():
        ranges[angle_name] = {"min": float('inf'), "max": float('-inf')}
        
    frame_count = 0
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)
            
            if results.pose_landmarks:
                angles = angle_calculator.calculate_cricket_angles(results.pose_landmarks)
                
                for angle_name, angle_data in angles.items():
                    val = angle_data["angle_degrees"]
                    # Only calculate if visibility is good
                    if val is not None and angle_data.get("status") == "ok":
                        if val < ranges[angle_name]["min"]:
                            ranges[angle_name]["min"] = val
                        if val > ranges[angle_name]["max"]:
                            ranges[angle_name]["max"] = val
                            
            if frame_count % 30 == 0:
                print(f"Processed {frame_count} frames...")
                
    cap.release()
    
    # Clean up defaults where pose wasn't found
    final_ranges = {}
    for k, v in ranges.items():
        if v["min"] != float('inf') and v["max"] != float('-inf'):
            final_ranges[k] = v
            
    # Save to JSON
    out_path = os.path.join(os.path.dirname(__file__), output_json)
    with open(out_path, "w") as f:
        json.dump(final_ranges, f, indent=4)
        
    print(f"Extraction complete! Saved ideal angles to: {out_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_ideal_angles.py <path_to_video.mp4>")
        sys.exit(1)
        
    extract_ideal(sys.argv[1])
