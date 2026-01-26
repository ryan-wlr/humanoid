"""
Configuration file for realistic robot simulation parameters.
Adjust these values to tune the realism of the simulation.
"""

# Physics Configuration
PHYSICS = {
    # Gravity in m/s² (Earth standard is -9.81)
    "gravity": -9.81,
    
    # Simulation time step in seconds (60 Hz = 1/60)
    "time_step": 1.0 / 60.0,
    
    # Ground friction coefficients
    "ground_static_friction": 0.5,
    "ground_dynamic_friction": 0.4,
    "ground_restitution": 0.01,  # Bounce coefficient
}

# Robot Configuration
ROBOT = {
    # Joint dynamics for realistic motion
    "joint_damping": 10.0,  # Newton-meters-second
    "joint_stiffness": 100.0,  # Newton-meters per radian
    
    # Gripper settings
    "gripper_force": 50.0,  # Force in Newtons
    "gripper_speed": 0.1,  # Closing speed in m/s
    
    # Motion planning
    "max_velocity": 0.5,  # Maximum end-effector velocity in m/s
    "max_acceleration": 1.0,  # Maximum acceleration in m/s²
}

# Object Configuration
OBJECTS = {
    # Apple properties (realistic for medium-sized apple)
    "apple": {
        "radius": 0.04,  # 8 cm diameter
        "mass": 0.2,  # 200 grams
        "color": [0.8, 0.1, 0.1],  # RGB red
        "position": [0.8, 0.0, 0.85],  # x, y, z in meters
        "friction": 0.6,  # Apple skin friction
    },
    
    # Desk properties (standard office desk)
    "desk": {
        "width": 1.2,  # meters
        "depth": 0.8,  # meters
        "height": 0.75,  # meters
        "mass": 20.0,  # kg
        "color": [0.6, 0.4, 0.2],  # RGB brown wood
        "position": [0.8, 0.0, 0.375],  # x, y, z in meters
        "is_static": True,  # Desk doesn't move
    },
}

# Behavior Configuration
BEHAVIOR = {
    # State machine timing (in seconds)
    "approach_duration": 2.0,
    "grasp_duration": 1.0,
    "lift_duration": 2.0,
    
    # Motion parameters
    "approach_offset": 0.15,  # Distance to stop before grasping (meters)
    "lift_height": 0.2,  # How high to lift apple (meters)
    
    # Safety parameters
    "collision_threshold": 0.05,  # Minimum distance to obstacles (meters)
    "force_threshold": 100.0,  # Maximum allowed force (Newtons)
}

# Rendering Configuration
RENDERING = {
    "enable_rendering": True,  # Set False for headless mode
    "render_fps": 60,  # Target rendering frame rate
    
    # Lighting
    "ambient_light_intensity": 1000,
    "sun_light_intensity": 3000,
    
    # Camera
    "camera_position": [2.0, 2.0, 1.5],  # x, y, z
    "camera_target": [0.8, 0.0, 0.5],  # Look at desk
}

# Simulation Configuration
SIMULATION = {
    "default_duration": 10.0,  # Default simulation time in seconds
    "real_time_factor": 1.0,  # Speed multiplier (1.0 = real-time)
    "enable_logging": True,  # Log simulation events
    "log_frequency": 10,  # Log every N frames
}

# Validation ranges for parameters (for safety checks)
VALIDATION = {
    "max_gripper_force": 200.0,  # Don't exceed 200 N
    "min_approach_offset": 0.05,  # At least 5 cm clearance
    "max_lift_height": 1.0,  # Don't lift more than 1 meter
}


def validate_config():
    """
    Validate configuration parameters are within safe ranges.
    
    Returns:
        tuple: (is_valid, error_messages)
    """
    errors = []
    
    # Check gripper force
    if ROBOT["gripper_force"] > VALIDATION["max_gripper_force"]:
        errors.append(
            f"Gripper force {ROBOT['gripper_force']} N exceeds maximum "
            f"{VALIDATION['max_gripper_force']} N"
        )
    
    # Check approach offset
    if BEHAVIOR["approach_offset"] < VALIDATION["min_approach_offset"]:
        errors.append(
            f"Approach offset {BEHAVIOR['approach_offset']} m is less than "
            f"minimum safe distance {VALIDATION['min_approach_offset']} m"
        )
    
    # Check lift height
    if BEHAVIOR["lift_height"] > VALIDATION["max_lift_height"]:
        errors.append(
            f"Lift height {BEHAVIOR['lift_height']} m exceeds maximum "
            f"{VALIDATION['max_lift_height']} m"
        )
    
    return len(errors) == 0, errors


def print_config():
    """Print current configuration in a readable format."""
    print("\n" + "=" * 70)
    print("REALISTIC ROBOT SIMULATION CONFIGURATION")
    print("=" * 70)
    
    print("\n🌍 PHYSICS")
    print(f"  Gravity: {PHYSICS['gravity']} m/s²")
    print(f"  Time step: {PHYSICS['time_step']:.4f} s ({1/PHYSICS['time_step']:.0f} Hz)")
    print(f"  Ground friction: {PHYSICS['ground_static_friction']} (static), "
          f"{PHYSICS['ground_dynamic_friction']} (dynamic)")
    
    print("\n🤖 ROBOT")
    print(f"  Joint damping: {ROBOT['joint_damping']} Nm·s")
    print(f"  Joint stiffness: {ROBOT['joint_stiffness']} Nm/rad")
    print(f"  Gripper force: {ROBOT['gripper_force']} N")
    print(f"  Max velocity: {ROBOT['max_velocity']} m/s")
    
    print("\n🍎 OBJECTS")
    apple = OBJECTS['apple']
    print(f"  Apple: {apple['mass']} kg, {apple['radius']*2*100:.1f} cm diameter")
    desk = OBJECTS['desk']
    print(f"  Desk: {desk['mass']} kg, {desk['width']}×{desk['depth']}×{desk['height']} m")
    
    print("\n🎬 BEHAVIOR")
    print(f"  Approach: {BEHAVIOR['approach_duration']} s")
    print(f"  Grasp: {BEHAVIOR['grasp_duration']} s")
    print(f"  Lift: {BEHAVIOR['lift_duration']} s")
    print(f"  Total time: {sum([BEHAVIOR['approach_duration'], BEHAVIOR['grasp_duration'], BEHAVIOR['lift_duration']])} s")
    
    print("\n" + "=" * 70)
    
    # Validate
    is_valid, errors = validate_config()
    if is_valid:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    print_config()
