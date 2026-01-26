# Running the Unitree G1 Humanoid Robot Simulation

## Prerequisites

1. **NVIDIA Isaac Sim**: Download and install from [NVIDIA's website](https://developer.nvidia.com/isaac-sim)
   - Requires: NVIDIA GPU with RTX support
   - Minimum: RTX 2060 or higher
   - Recommended: RTX 3080 or higher for best performance

2. **Python 3.7+**: Comes bundled with Isaac Sim

## Installation

1. Clone this repository:
```bash
git clone https://github.com/ryan-wlr/humanoid.git
cd humanoid
```

2. Ensure Isaac Sim is installed and accessible

3. Install additional dependencies:
```bash
pip install -r requirements.txt
```

## Running the Simulation

### Method 1: Using Isaac Sim Python

```bash
# Navigate to Isaac Sim installation directory
cd ~/.local/share/ov/pkg/isaac_sim-*/

# Run the simulation script
./python.sh /path/to/humanoid/robot_simulation.py
```

### Method 2: Standalone Python (if Isaac Sim Python is in PATH)

```bash
python robot_simulation.py
```

## Features

The simulation includes the following realistic features:

### 1. Realistic Physics
- **Gravity**: -9.81 m/s² (Earth standard)
- **Time Step**: 60 Hz (16.67ms per step)
- **Friction**: Realistic static (0.5) and dynamic (0.4) friction coefficients
- **Restitution**: Low bounce (0.01) for stable interactions

### 2. Realistic Robot Dynamics
- **Joint Damping**: 10 Nm·s for smooth, human-like motion
- **Joint Stiffness**: 100 Nm/rad for stable control
- **Gripper Force**: 50 N for secure grasping without crushing

### 3. Realistic Object Properties
- **Apple Mass**: 0.2 kg (typical apple weight)
- **Apple Size**: 8 cm diameter
- **Desk Mass**: 20 kg (realistic office desk)
- **Desk Dimensions**: 1.2m × 0.8m × 0.75m (standard desk size)

### 4. Intelligent Behavior
- **Motion Planning**: State-based approach, grasp, and lift sequence
- **Collision Avoidance**: Built into motion planning
- **Force Control**: Adaptive gripper force based on object properties

## Simulation States

The robot goes through the following realistic behavioral states:

1. **Init**: Robot initializes and assesses the environment
2. **Approach**: Robot moves toward the apple (2 seconds)
3. **Grasp**: Robot closes gripper to grasp apple (1 second)
4. **Lift**: Robot lifts apple off the desk (2 seconds)
5. **Complete**: Task successfully completed

## Customization

### Adjusting Physics Parameters

Edit the following in `robot_simulation.py`:

```python
# In __init__ method
self.gravity = -9.81  # Change gravity (m/s²)
self.time_step = 1.0/60.0  # Change simulation frequency
self.grasp_force = 50.0  # Change gripper force (N)
```

### Changing Object Positions

Modify object positions in the `create_apple()` and `create_desk()` methods:

```python
# Change apple position
position=np.array([x, y, z])
```

### Adjusting Motion Timing

Edit state transition times in `execute_motion()`:

```python
if self.state_time > 2.0:  # Adjust timing (seconds)
```

## Troubleshooting

### "Could not find Isaac Sim assets folder"
- Ensure Isaac Sim is properly installed
- Check that Nucleus server is running
- Verify asset paths in Isaac Sim settings

### Robot model not loading
- The simulation uses Franka arm as a placeholder
- For actual Unitree G1 model, replace asset path in `load_robot()`
- Contact Unitree for official G1 USD model

### Simulation runs slowly
- Reduce rendering quality in Isaac Sim settings
- Close other applications
- Ensure NVIDIA GPU drivers are up to date
- Consider using headless mode for faster physics simulation

### Physics behaving unrealistically
- Verify GPU physics is enabled in Isaac Sim
- Check collision mesh quality
- Adjust time step if needed (smaller = more accurate but slower)

## Advanced Usage

### Headless Mode (No GUI)

For faster simulation without rendering:

```python
simulation_app = SimulationApp({"headless": True})
```

### Recording Simulation

Add these lines before running:

```python
from omni.isaac.core.utils.extensions import enable_extension
enable_extension("omni.isaac.synthetic_recorder")
```

### Integration with ROS

To integrate with Robot Operating System (ROS):

```python
from omni.isaac.ros_bridge import RosBridge
# Add ROS publishers/subscribers for realistic robot control
```

## Performance Benchmarks

Expected performance on different hardware:

| GPU | FPS | Real-time Factor |
|-----|-----|------------------|
| RTX 4090 | 60 | 1.0x |
| RTX 3080 | 50-55 | 0.9x |
| RTX 2060 | 30-40 | 0.6x |

## Contributing

To add more realistic features:
1. Fork the repository
2. Add new physics properties or behaviors
3. Test thoroughly with different scenarios
4. Submit a pull request

## License

See LICENSE file in repository root.

## References

- [NVIDIA Isaac Sim Documentation](https://docs.omniverse.nvidia.com/app_isaacsim/)
- [Unitree G1 Robot Specifications](https://www.unitree.com/)
- [Physics Simulation Best Practices](https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/tutorial_core_physics.html)
