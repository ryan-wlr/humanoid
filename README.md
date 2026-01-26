# Humanoid Robot Simulation

A realistic simulation of the Unitree G1 humanoid robot in NVIDIA Isaac Sim. The robot performs an apple-grasping task with realistic physics, dynamics, and motion planning.

## Features

This simulation implements a highly realistic robotic system with the following features:

### 🎯 Realistic Physics
- **Accurate gravity**: Standard Earth gravity (-9.81 m/s²)
- **High-frequency simulation**: 60 Hz time steps for smooth motion
- **Realistic friction**: Separate static (0.5) and dynamic (0.4) coefficients
- **Material properties**: Proper restitution values for realistic collisions

### 🤖 Advanced Robot Dynamics
- **Joint damping**: 10 Nm·s for human-like smooth movements
- **Joint stiffness**: 100 Nm/rad for stable position control
- **Force control**: 50 N gripper force optimized for delicate object manipulation
- **Motion planning**: Intelligent state-based behavior system

### 🍎 Realistic Objects
- **Apple**: Accurate 0.2 kg mass and 8 cm diameter
- **Desk**: Standard office desk (1.2m × 0.8m × 0.75m, 20 kg)
- **Proper materials**: Realistic colors and physical properties

### 🧠 Intelligent Behavior
- **State machine**: Init → Approach → Grasp → Lift → Complete
- **Motion planning**: Calculated trajectories with collision avoidance
- **Adaptive control**: Force-based grasping for secure object handling

## Quick Start

```bash
# Install NVIDIA Isaac Sim first
# Then run:
./python.sh robot_simulation.py
```

See [USAGE.md](USAGE.md) for detailed installation and usage instructions.

## Files

- `robot_simulation.py` - Main simulation script with realistic robot control
- `requirements.txt` - Python dependencies
- `USAGE.md` - Comprehensive documentation and troubleshooting guide

## Requirements

- NVIDIA Isaac Sim 2022.1 or later
- NVIDIA GPU with RTX support (RTX 2060 or better)
- Python 3.7+
- NumPy 1.21+

## What Makes This Realistic?

1. **Physics Accuracy**: Uses real-world values for gravity, friction, and object properties
2. **Human-like Motion**: Joint damping and stiffness tuned for smooth, natural movements
3. **Proper Scaling**: All objects sized and weighted realistically
4. **Intelligent Planning**: State-based behavior that mimics human task execution
5. **Force Control**: Gripper applies appropriate force without crushing objects

## Performance

Runs at real-time (60 FPS) on RTX 3080 or better. See USAGE.md for detailed benchmarks.

## License

MIT License - See LICENSE file for details.
