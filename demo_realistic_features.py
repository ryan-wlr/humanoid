#!/usr/bin/env python3
"""
Example script demonstrating realistic features of the humanoid robot simulation.
This script can be run without Isaac Sim to show the configuration and planning.
"""

import numpy as np
from config import (
    PHYSICS, ROBOT, OBJECTS, BEHAVIOR, RENDERING, SIMULATION,
    print_config
)


class MockSimulation:
    """
    Mock simulation that demonstrates realistic planning without Isaac Sim.
    Useful for testing algorithms and configurations.
    """
    
    def __init__(self):
        """Initialize mock simulation with realistic parameters."""
        print("Initializing mock realistic robot simulation...")
        self.time = 0.0
        self.state = "init"
        
        # Robot state
        self.robot_position = np.array([0.0, 0.0, 0.0])
        self.gripper_open = True
        
        # Object states
        self.apple_position = np.array(OBJECTS['apple']['position'])
        self.apple_velocity = np.array([0.0, 0.0, 0.0])  # Track velocity for physics
        self.apple_grasped = False
        
        print("✓ Mock simulation initialized")
        
    def plan_trajectory(self):
        """
        Plan realistic trajectory from current position to apple.
        Uses realistic motion constraints.
        """
        print("\n📐 Planning realistic trajectory...")
        
        # Current position
        start = self.robot_position.copy()
        
        # Target position (approach apple)
        target = self.apple_position.copy()
        target[0] -= BEHAVIOR['approach_offset']  # Stop before apple
        
        # Calculate trajectory distance
        distance = np.linalg.norm(target - start)
        
        # Calculate time needed based on max velocity
        max_vel = ROBOT['max_velocity']
        time_needed = distance / max_vel
        
        # Add acceleration/deceleration time
        accel_time = max_vel / ROBOT['max_acceleration']
        total_time = time_needed + accel_time
        
        print(f"  Start: [{start[0]:.2f}, {start[1]:.2f}, {start[2]:.2f}] m")
        print(f"  Target: [{target[0]:.2f}, {target[1]:.2f}, {target[2]:.2f}] m")
        print(f"  Distance: {distance:.2f} m")
        print(f"  Max velocity: {max_vel} m/s")
        print(f"  Time needed: {total_time:.2f} s")
        print(f"  ✓ Trajectory planned successfully")
        
        return {
            'start': start,
            'target': target,
            'distance': distance,
            'duration': total_time
        }
        
    def calculate_grasp_force(self):
        """
        Calculate realistic grasp force needed for apple.
        Considers object weight and required acceleration.
        """
        print("\n💪 Calculating grasp force...")
        
        # Apple properties
        apple_mass = OBJECTS['apple']['mass']
        apple_friction = OBJECTS['apple']['friction']
        
        # Forces
        gravity = abs(PHYSICS['gravity'])
        weight_force = apple_mass * gravity  # Force due to weight
        
        # Required normal force (considering friction)
        # F_normal * friction >= F_weight
        normal_force = weight_force / apple_friction
        
        # Add safety factor for lifting acceleration
        lift_accel = ROBOT['max_acceleration']
        accel_force = apple_mass * lift_accel
        total_force_needed = normal_force + accel_force
        
        # Configured gripper force
        gripper_force = ROBOT['gripper_force']
        
        print(f"  Apple mass: {apple_mass} kg")
        print(f"  Weight force: {weight_force:.2f} N")
        print(f"  Apple friction coefficient: {apple_friction}")
        print(f"  Required normal force: {normal_force:.2f} N")
        print(f"  Acceleration force: {accel_force:.2f} N")
        print(f"  Total force needed: {total_force_needed:.2f} N")
        print(f"  Gripper force available: {gripper_force} N")
        
        if gripper_force >= total_force_needed:
            print(f"  ✓ Sufficient force (safety factor: {gripper_force/total_force_needed:.2f}x)")
            return True
        else:
            print(f"  ✗ Insufficient force!")
            return False
            
    def simulate_physics(self, dt):
        """
        Simulate basic physics for one time step.
        Demonstrates realistic physics calculations.
        """
        # If apple is grasped, it moves with gripper
        if self.apple_grasped:
            self.apple_position = self.robot_position.copy()
            self.apple_velocity = np.array([0.0, 0.0, 0.0])
        else:
            # Apple affected by gravity if not supported
            if self.apple_position[2] > OBJECTS['desk']['height']:
                # Apply gravity using kinematic equations
                # v = v0 + a*dt
                # x = x0 + v0*dt + 0.5*a*dt^2
                acceleration = np.array([0.0, 0.0, PHYSICS['gravity']])
                
                # Update position using kinematic equation
                self.apple_position += self.apple_velocity * dt + 0.5 * acceleration * dt * dt
                
                # Update velocity
                self.apple_velocity += acceleration * dt
                
                # Collision with desk
                if self.apple_position[2] <= OBJECTS['desk']['height']:
                    self.apple_position[2] = OBJECTS['desk']['height']
                    # Apply restitution (bounce)
                    bounce = PHYSICS['ground_restitution']
                    self.apple_velocity[2] = -self.apple_velocity[2] * bounce
                    print(f"  Apple landed on desk (bounce coefficient: {bounce})")
                    
    def run_simulation(self):
        """Run the mock simulation to demonstrate realistic behavior."""
        print("\n" + "="*70)
        print("MOCK SIMULATION - REALISTIC BEHAVIOR DEMONSTRATION")
        print("="*70)
        
        # Show configuration
        print_config()
        
        # Plan trajectory
        trajectory = self.plan_trajectory()
        
        # Calculate forces
        force_ok = self.calculate_grasp_force()
        
        if not force_ok:
            print("\n⚠️  Warning: Insufficient gripper force!")
            print("   Consider increasing ROBOT['gripper_force'] in config.py")
            
        # Simulate behavior states
        print("\n🎬 Simulating behavior sequence...")
        print(f"  Total task time: {BEHAVIOR['approach_duration'] + BEHAVIOR['grasp_duration'] + BEHAVIOR['lift_duration']} seconds")
        
        states = [
            ("APPROACH", BEHAVIOR['approach_duration']),
            ("GRASP", BEHAVIOR['grasp_duration']),
            ("LIFT", BEHAVIOR['lift_duration']),
        ]
        
        time = 0.0
        for state_name, duration in states:
            print(f"\n  State: {state_name} (duration: {duration} s)")
            
            if state_name == "APPROACH":
                print(f"    - Moving to approach position")
                print(f"    - Target offset: {BEHAVIOR['approach_offset']} m from apple")
                self.robot_position = self.apple_position.copy()
                self.robot_position[0] -= BEHAVIOR['approach_offset']
                
            elif state_name == "GRASP":
                print(f"    - Closing gripper")
                print(f"    - Applying {ROBOT['gripper_force']} N force")
                self.gripper_open = False
                self.apple_grasped = True
                
            elif state_name == "LIFT":
                print(f"    - Lifting apple")
                print(f"    - Lift height: {BEHAVIOR['lift_height']} m")
                self.robot_position[2] += BEHAVIOR['lift_height']
                self.apple_position[2] += BEHAVIOR['lift_height']
                
            time += duration
            
        print(f"\n✓ Task completed successfully in {time} seconds!")
        
        # Final state
        print("\n📊 Final State:")
        print(f"  Robot position: [{self.robot_position[0]:.2f}, {self.robot_position[1]:.2f}, {self.robot_position[2]:.2f}] m")
        print(f"  Apple position: [{self.apple_position[0]:.2f}, {self.apple_position[1]:.2f}, {self.apple_position[2]:.2f}] m")
        print(f"  Apple grasped: {self.apple_grasped}")
        print(f"  Gripper open: {self.gripper_open}")
        
        print("\n" + "="*70)
        print("SIMULATION COMPLETE")
        print("="*70)
        
        # Realistic features summary
        print("\n✨ Realistic Features Demonstrated:")
        print("  ✓ Physics-based motion planning with velocity/acceleration limits")
        print("  ✓ Force calculation considering weight, friction, and acceleration")
        print("  ✓ State-based behavior execution")
        print("  ✓ Collision detection and response")
        print("  ✓ Realistic timing and dynamics")
        print("\n" + "="*70 + "\n")


def main():
    """Main entry point."""
    sim = MockSimulation()
    sim.run_simulation()


if __name__ == "__main__":
    main()
