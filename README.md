# Unitree G1 Robot - Apple Grabbing Simulation

This project implements a simulation of the Unitree G1 humanoid robot in NVIDIA Isaac Sim, demonstrating autonomous apple grabbing from a desk surface using manipulation and grasping capabilities.

## Overview

The Unitree G1 robot is programmed to:
1. Detect an apple placed on a desk
2. Plan a trajectory to reach the apple
3. Grasp the apple using its end-effector
4. Lift the apple
5. Retract to a neutral position

## Features

- **Full Isaac Sim Integration**: Leverages NVIDIA Isaac Sim's physics engine and rendering
- **State Machine Controller**: Robust state-based control system for manipulation
- **Object Detection**: Position-based apple detection (extensible to vision-based)
- **Modular Design**: Separate modules for simulation, control, and detection
- **Configurable**: YAML-based configuration for easy parameter tuning

## Project Structure

```
humanoid/
├── scripts/              # Main Python scripts
│   ├── simulation.py          # Main simulation entry point
│   ├── robot_controller.py    # State machine controller
│   └── object_detection.py    # Apple detection module
├── config/              # Configuration files
│   ├── robot_config.yaml      # Robot parameters
│   └── scene_config.yaml      # Scene setup parameters
├── launch/              # Launch scripts
│   └── g1_manipulation.launch.py
├── assets/              # 3D models and resources (to be added)
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Prerequisites

### Required Software

1. **NVIDIA Omniverse** (Latest version)
2. **Isaac Sim** (2022.2.0 or later)
   - Download from [NVIDIA Omniverse](https://www.nvidia.com/en-us/omniverse/)
   - Install through Omniverse Launcher

3. **System Requirements**
   - Ubuntu 20.04/22.04 or Windows 10/11
   - NVIDIA RTX GPU (recommended: RTX 3060 or better)
   - 32GB RAM (recommended)
   - 50GB free disk space

### Python Dependencies

```bash
pip install -r requirements.txt
```

Note: Isaac Sim includes its own Python environment with necessary packages pre-installed.

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ryan-wlr/humanoid.git
   cd humanoid
   ```

2. **Install Isaac Sim**
   - Follow NVIDIA's official installation guide
   - Verify installation by launching Isaac Sim

3. **Configure paths** (if needed)
   - Update asset paths in configuration files
   - Ensure Isaac Sim Python is accessible

## Usage

### Running the Simulation

#### Method 1: Using Isaac Sim's Python

```bash
# Navigate to Isaac Sim installation directory
cd ~/.local/share/ov/pkg/isaac_sim-*

# Run the launch script
./python.sh /path/to/humanoid/launch/g1_manipulation.launch.py
```

#### Method 2: Direct execution

```bash
cd humanoid/scripts
python simulation.py
```

#### Method 3: From Isaac Sim GUI

1. Open Isaac Sim
2. Go to `Window > Script Editor`
3. Load and run `scripts/simulation.py`

### Configuration

Edit configuration files in the `config/` directory:

**Robot Configuration** (`config/robot_config.yaml`):
- Adjust robot parameters
- Modify control gains
- Set initial pose

**Scene Configuration** (`config/scene_config.yaml`):
- Change desk/apple positions
- Adjust object properties
- Configure camera and lighting

## How It Works

### State Machine

The robot controller implements a finite state machine with the following states:

1. **IDLE**: Initial state, waiting to start
2. **APPROACHING**: Moving arm towards the apple
3. **GRASPING**: Closing gripper on the apple
4. **LIFTING**: Lifting the apple upward
5. **RETRACTING**: Moving arm back to neutral
6. **DONE**: Task complete

### Control Pipeline

```
Simulation Loop
    ↓
Object Detection → Get Apple Position
    ↓
State Machine → Determine Current Action
    ↓
Controller → Generate Joint Commands
    ↓
Robot → Execute Motion
    ↓
Physics Engine → Simulate & Render
```

## Development

### VS Code Integration

This project is designed to work with VS Code and GitHub Copilot:

1. Open the project in VS Code
2. Install recommended extensions:
   - Python
   - GitHub Copilot
   - YAML

3. Use Copilot for:
   - Code suggestions
   - Documentation
   - Debugging assistance

### Adding Features

- **Vision-based detection**: Enhance `object_detection.py` with camera sensors
- **IK Solver**: Replace simplified kinematics with proper inverse kinematics
- **Multiple objects**: Extend to handle multiple apples or different objects
- **Force control**: Add force-feedback for adaptive grasping

### Testing

```bash
# Run simulation in headless mode for testing
python launch/g1_manipulation.launch.py --headless
```

## Troubleshooting

### Common Issues

1. **"Module 'omni.isaac' not found"**
   - Solution: Run using Isaac Sim's Python interpreter

2. **Robot model not loading**
   - Solution: Check asset paths in configuration files
   - Verify Isaac Sim asset library is accessible

3. **Simulation runs slowly**
   - Solution: Reduce physics timestep or disable rendering
   - Check GPU drivers are up to date

4. **Gripper not grasping**
   - Solution: Adjust grasp force in `robot_config.yaml`
   - Verify collision geometry is correct

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is provided as-is for educational and research purposes.

## Acknowledgments

- NVIDIA Isaac Sim team for the simulation platform
- Unitree Robotics for the G1 robot design
- GitHub Copilot for development assistance

## Contact

For questions or issues, please open an issue on GitHub.

---

**Note**: This simulation uses a placeholder robot model. For production use with an actual Unitree G1, you'll need to:
1. Obtain the official G1 USD/URDF model
2. Update asset paths in the code
3. Calibrate control parameters for the real robot
