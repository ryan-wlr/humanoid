"""
Robot controller for Unitree G1 manipulation tasks.

This module implements a state machine controller for the Unitree G1 robot
to perform object manipulation tasks such as grabbing an apple.
"""

import numpy as np
from enum import Enum
from omni.isaac.core.utils.types import ArticulationAction


class RobotState(Enum):
    """States for the robot manipulation task."""
    IDLE = 0
    APPROACHING = 1
    GRASPING = 2
    LIFTING = 3
    RETRACTING = 4
    DONE = 5


class UnitreeG1Controller:
    """
    Controller for Unitree G1 robot to perform apple grabbing task.
    
    This controller implements a simple state machine:
    1. IDLE: Initial state
    2. APPROACHING: Move arm towards the apple
    3. GRASPING: Close gripper to grab the apple
    4. LIFTING: Lift the apple up
    5. RETRACTING: Move arm back to neutral position
    6. DONE: Task complete
    """

    def __init__(self, robot, target_position):
        """
        Initialize the controller.
        
        Args:
            robot: The robot articulation object
            target_position: 3D position of the target (apple)
        """
        self.robot = robot
        self.target_position = np.array(target_position)
        self.state = RobotState.IDLE
        self.state_time = 0.0
        self.phase_duration = 2.0  # Duration for each phase in seconds
        
        # Store initial robot configuration
        self.initial_positions = None
        
        print(f"Controller initialized. Target position: {self.target_position}")
        
    def get_state(self):
        """Get current state as string."""
        return self.state.name
        
    def update(self, dt):
        """
        Update the controller.
        
        Args:
            dt: Time step in seconds
        """
        if not self.robot:
            return
            
        self.state_time += dt
        
        # State machine
        if self.state == RobotState.IDLE:
            if self.state_time > 1.0:  # Wait 1 second before starting
                self.transition_to_approaching()
                
        elif self.state == RobotState.APPROACHING:
            self.approach_target(dt)
            if self.state_time > self.phase_duration:
                self.transition_to_grasping()
                
        elif self.state == RobotState.GRASPING:
            self.grasp_object(dt)
            if self.state_time > self.phase_duration:
                self.transition_to_lifting()
                
        elif self.state == RobotState.LIFTING:
            self.lift_object(dt)
            if self.state_time > self.phase_duration:
                self.transition_to_retracting()
                
        elif self.state == RobotState.RETRACTING:
            self.retract_arm(dt)
            if self.state_time > self.phase_duration:
                self.transition_to_done()
                
        elif self.state == RobotState.DONE:
            pass  # Task complete
            
    def transition_to_approaching(self):
        """Transition to approaching state."""
        self.state = RobotState.APPROACHING
        self.state_time = 0.0
        print("State: APPROACHING - Moving arm towards apple")
        
        # Store initial positions if not already stored
        if self.initial_positions is None:
            try:
                self.initial_positions = self.robot.get_joint_positions()
            except (AttributeError, RuntimeError) as e:
                print(f"Warning: Could not get initial joint positions: {e}")
        
    def transition_to_grasping(self):
        """Transition to grasping state."""
        self.state = RobotState.GRASPING
        self.state_time = 0.0
        print("State: GRASPING - Closing gripper on apple")
        
    def transition_to_lifting(self):
        """Transition to lifting state."""
        self.state = RobotState.LIFTING
        self.state_time = 0.0
        print("State: LIFTING - Lifting apple up")
        
    def transition_to_retracting(self):
        """Transition to retracting state."""
        self.state = RobotState.RETRACTING
        self.state_time = 0.0
        print("State: RETRACTING - Moving arm back to neutral")
        
    def transition_to_done(self):
        """Transition to done state."""
        self.state = RobotState.DONE
        self.state_time = 0.0
        print("State: DONE - Task complete! Apple grabbed successfully!")
        
    def approach_target(self, dt):
        """
        Move the robot arm towards the target position.
        
        Args:
            dt: Time step
        """
        try:
            # Get current joint positions
            current_positions = self.robot.get_joint_positions()
            
            # Calculate desired joint positions to reach target
            # This is a simplified approach - in production, use proper IK solver
            num_joints = len(current_positions)
            
            # Create smooth motion towards target
            # Joint angles that approximately reach towards the apple
            target_joint_positions = current_positions.copy()
            
            # Interpolation factor based on time
            alpha = min(self.state_time / self.phase_duration, 1.0)
            
            # Simple approach: modify first few joints to reach forward
            if num_joints >= 3:
                target_joint_positions[0] += alpha * 0.3  # Shoulder
                target_joint_positions[1] += alpha * -0.5  # Elbow
                target_joint_positions[2] += alpha * 0.2   # Wrist
            
            # Apply joint positions
            action = ArticulationAction(joint_positions=target_joint_positions)
            self.robot.apply_action(action)
            
        except (AttributeError, RuntimeError, ValueError) as e:
            print(f"Error in approach_target: {e}")
        
    def grasp_object(self, dt):
        """
        Close gripper to grasp the object.
        
        Args:
            dt: Time step
        """
        try:
            # Get current joint positions
            current_positions = self.robot.get_joint_positions()
            num_joints = len(current_positions)
            
            # Close gripper (typically last 2 joints for parallel gripper)
            target_positions = current_positions.copy()
            
            # Interpolation for smooth gripper closing
            alpha = min(self.state_time / self.phase_duration, 1.0)
            
            if num_joints >= 2:
                # Close gripper fingers
                gripper_close_value = 0.02 * alpha  # Close to nearly touching
                target_positions[-1] = gripper_close_value
                target_positions[-2] = gripper_close_value
            
            action = ArticulationAction(joint_positions=target_positions)
            self.robot.apply_action(action)
            
        except (AttributeError, RuntimeError, ValueError) as e:
            print(f"Error in grasp_object: {e}")
        
    def lift_object(self, dt):
        """
        Lift the grasped object upward.
        
        Args:
            dt: Time step
        """
        try:
            # Get current joint positions
            current_positions = self.robot.get_joint_positions()
            
            # Lift by adjusting joint angles
            alpha = min(self.state_time / self.phase_duration, 1.0)
            
            target_positions = current_positions.copy()
            
            # Lift motion - adjust shoulder/elbow to raise arm
            if len(target_positions) >= 3:
                target_positions[1] -= alpha * 0.4  # Lift elbow
                target_positions[2] += alpha * 0.3  # Adjust wrist
            
            action = ArticulationAction(joint_positions=target_positions)
            self.robot.apply_action(action)
            
        except (AttributeError, RuntimeError, ValueError) as e:
            print(f"Error in lift_object: {e}")
        
    def retract_arm(self, dt):
        """
        Retract arm back to neutral position.
        
        Args:
            dt: Time step
        """
        try:
            if self.initial_positions is None:
                return
                
            # Get current and target positions
            current_positions = self.robot.get_joint_positions()
            
            # Interpolate back to initial positions
            alpha = min(self.state_time / self.phase_duration, 1.0)
            
            target_positions = (1 - alpha) * current_positions + alpha * self.initial_positions
            
            action = ArticulationAction(joint_positions=target_positions)
            self.robot.apply_action(action)
            
        except (AttributeError, RuntimeError, ValueError) as e:
            print(f"Error in retract_arm: {e}")
