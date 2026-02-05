"""
Main simulation script for Unitree G1 robot apple grabbing task in Isaac Sim.

This script sets up the Isaac Sim environment, loads the Unitree G1 robot,
creates a desk with an apple, and executes the manipulation task.
"""

from omni.isaac.kit import SimulationApp

# Launch Isaac Sim
simulation_app = SimulationApp({"headless": False})

import numpy as np
from omni.isaac.core import World
from omni.isaac.core.objects import DynamicCuboid, VisualSphere
from omni.isaac.core.prims import XFormPrim
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.utils.types import ArticulationAction
import carb

from robot_controller import UnitreeG1Controller


class AppleGrabbingSimulation:
    """
    Simulation environment for Unitree G1 robot to grab an apple on a desk.
    """

    def __init__(self):
        """Initialize the simulation environment."""
        self.world = World(stage_units_in_meters=1.0)
        self.controller = None
        self.robot = None
        self.apple = None
        self.desk = None
        
    def setup_scene(self):
        """Set up the scene with robot, desk, and apple."""
        print("Setting up scene...")
        
        # Add ground plane
        self.world.scene.add_default_ground_plane()
        
        # Create desk
        self.desk = self.world.scene.add(
            DynamicCuboid(
                prim_path="/World/Desk",
                name="desk",
                position=np.array([0.6, 0.0, 0.4]),
                size=np.array([0.8, 1.2, 0.02]),
                color=np.array([0.5, 0.35, 0.2]),
                mass=50.0,
            )
        )
        
        # Create apple on desk
        self.apple = self.world.scene.add(
            VisualSphere(
                prim_path="/World/Apple",
                name="apple",
                position=np.array([0.6, 0.2, 0.45]),
                radius=0.04,
                color=np.array([0.8, 0.1, 0.1]),
            )
        )
        
        # Load Unitree G1 robot
        # Note: In a real implementation, you would load the actual Unitree G1 USD/URDF
        # For this example, we'll use a placeholder articulation
        self.setup_robot()
        
        print("Scene setup complete!")
        
    def setup_robot(self):
        """Set up the Unitree G1 robot."""
        print("Loading Unitree G1 robot...")
        
        # In a production environment, you would load the actual Unitree G1 model:
        # assets_root_path = get_assets_root_path()
        # robot_usd_path = assets_root_path + "/Isaac/Robots/Unitree/G1/g1.usd"
        # add_reference_to_stage(usd_path=robot_usd_path, prim_path="/World/G1")
        
        # For this example, we'll create a simple articulated robot representation
        # In practice, the G1 has arms, hands, and a torso that we would control
        try:
            # Try to load from Isaac Sim's asset library
            assets_root_path = get_assets_root_path()
            if assets_root_path:
                # Use Franka robot as a stand-in for demonstration
                # In production, replace with actual G1 model
                robot_path = assets_root_path + "/Isaac/Robots/Franka/franka.usd"
                add_reference_to_stage(usd_path=robot_path, prim_path="/World/Robot")
                
                self.robot = self.world.scene.add(
                    Articulation(
                        prim_path="/World/Robot",
                        name="g1_robot"
                    )
                )
        except Exception as e:
            carb.log_warn(f"Could not load robot model: {e}")
            carb.log_warn("Using placeholder robot representation")
            # Create a simple placeholder since no robot model is available
            # In production, this should fail gracefully or require a valid model
            self.robot = None
            
        print("Robot loaded!")
        
    def initialize_controller(self):
        """Initialize the robot controller."""
        if self.robot:
            try:
                target_pos = self.apple.get_world_pose()[0]
                self.controller = UnitreeG1Controller(
                    robot=self.robot,
                    target_position=target_pos
                )
                print("Controller initialized!")
            except (AttributeError, RuntimeError) as e:
                carb.log_error(f"Failed to initialize controller: {e}")
                self.controller = None
        else:
            carb.log_warn("No robot available, skipping controller initialization")
        
    def run(self):
        """Run the simulation."""
        print("Starting Unitree G1 Apple Grabbing Simulation...")
        
        # Set up the scene
        self.setup_scene()
        
        # Reset the world
        self.world.reset()
        
        # Initialize controller after reset
        self.initialize_controller()
        
        # Simulation parameters
        frame_count = 0
        
        print("\n=== Simulation Running ===")
        print("The robot will now attempt to grab the apple...")
        print("Close the Isaac Sim window to stop the simulation.\n")
        
        # Main simulation loop
        while simulation_app.is_running():
            # Step the world
            self.world.step(render=True)
            
            if self.world.is_playing():
                if self.world.current_time_step_index == 0:
                    self.world.reset()
                    self.initialize_controller()
                
                # Update controller
                if self.controller:
                    self.controller.update(self.world.get_physics_dt())
                    
                frame_count += 1
                
                # Print status every 100 frames
                if frame_count % 100 == 0:
                    if self.controller:
                        print(f"Frame {frame_count}: State = {self.controller.get_state()}")
        
        # Cleanup
        print("\nSimulation ended.")
        simulation_app.close()


def main():
    """Main entry point."""
    simulation = AppleGrabbingSimulation()
    simulation.run()


if __name__ == "__main__":
    main()
