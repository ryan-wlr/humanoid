"""
Object detection module for identifying and localizing the apple in the scene.

This module provides functionality to detect objects (like apples) in the
Isaac Sim environment using position-based detection.
"""

import numpy as np
from typing import Optional, Tuple


class AppleDetector:
    """
    Simple object detector for the apple in the scene.
    
    In a production environment, this could be enhanced with:
    - Camera-based vision detection
    - RGB-D sensing
    - Object recognition networks
    - Point cloud processing
    """
    
    def __init__(self, apple_prim):
        """
        Initialize the detector.
        
        Args:
            apple_prim: The apple object primitive from Isaac Sim
        """
        self.apple = apple_prim
        self.last_position = None
        
    def detect(self) -> Optional[Tuple[np.ndarray, bool]]:
        """
        Detect the apple in the scene.
        
        Returns:
            Tuple of (position, detected) or None if detection fails
            - position: 3D numpy array [x, y, z] in world coordinates
            - detected: Boolean indicating if apple was detected
        """
        try:
            # Get apple position from the scene
            position, _ = self.apple.get_world_pose()
            self.last_position = position
            
            return position, True
        except Exception as e:
            print(f"Detection error: {e}")
            return None, False
    
    def get_grasp_pose(self) -> Optional[np.ndarray]:
        """
        Calculate the grasp pose for the apple.
        
        Returns:
            4x4 transformation matrix for grasping, or None if not detected
        """
        detection = self.detect()
        if detection[1]:
            position = detection[0]
            
            # Simple grasp pose: approach from above
            grasp_position = position.copy()
            grasp_position[2] += 0.1  # Approach from 10cm above
            
            return grasp_position
        
        return None
    
    def is_grasped(self, gripper_position: np.ndarray, threshold: float = 0.05) -> bool:
        """
        Check if the apple is currently grasped.
        
        Args:
            gripper_position: Current position of the gripper
            threshold: Distance threshold for considering object grasped
            
        Returns:
            Boolean indicating if apple is grasped
        """
        if self.last_position is None:
            return False
        
        distance = np.linalg.norm(gripper_position - self.last_position)
        return distance < threshold
    
    def get_distance_to_target(self, current_position: np.ndarray) -> float:
        """
        Calculate distance from current position to apple.
        
        Args:
            current_position: Current end-effector position
            
        Returns:
            Euclidean distance in meters
        """
        if self.last_position is None:
            detection = self.detect()
            if not detection[1]:
                return float('inf')
        
        return np.linalg.norm(current_position - self.last_position)
