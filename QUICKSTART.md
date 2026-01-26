# Quick Start Guide

Get the Unitree G1 Apple Grabbing simulation running in just a few steps!

## Prerequisites Check

Before starting, ensure you have:
- [ ] NVIDIA GPU (RTX series recommended)
- [ ] Ubuntu 20.04/22.04 or Windows 10/11
- [ ] 32GB RAM minimum
- [ ] NVIDIA Omniverse installed
- [ ] Isaac Sim installed via Omniverse

## Step-by-Step Setup

### 1. Verify Installation

First, verify that all project files are in place:

```bash
cd humanoid
python scripts/verify_setup.py
```

You should see all checks passing with ✓ marks.

### 2. Locate Isaac Sim

Find your Isaac Sim installation directory. Typical locations:

**Linux:**
```bash
~/.local/share/ov/pkg/isaac_sim-2023.1.1/
```

**Windows:**
```
C:\Users\<username>\AppData\Local\ov\pkg\isaac_sim-2023.1.1\
```

### 3. Run the Simulation

**On Linux:**
```bash
cd humanoid
~/.local/share/ov/pkg/isaac_sim-*/python.sh launch/g1_manipulation.launch.py
```

**On Windows:**
```cmd
cd humanoid
C:\Users\<username>\AppData\Local\ov\pkg\isaac_sim-2023.1.1\python.bat launch\g1_manipulation.launch.py
```

### 4. What to Expect

When the simulation starts, you will see:

1. **Isaac Sim window opens** - The 3D viewport loads
2. **Scene creation** - Desk and apple appear in the scene
3. **Robot loads** - The robot model is placed in the scene
4. **Simulation starts** - The robot begins its manipulation task
5. **Console output** - Status messages show the robot's state

The robot will go through these states:
- IDLE → APPROACHING → GRASPING → LIFTING → RETRACTING → DONE

## Troubleshooting

### "ModuleNotFoundError: No module named 'omni'"

**Solution**: You must use Isaac Sim's Python interpreter, not your system Python.

```bash
# ✗ Wrong
python scripts/simulation.py

# ✓ Correct
~/.local/share/ov/pkg/isaac_sim-*/python.sh scripts/simulation.py
```

### Simulation window is black or frozen

**Solution**: 
1. Check GPU drivers are updated
2. Verify your GPU meets requirements
3. Try reducing the viewport resolution

### Robot model not appearing

**Solution**: The simulation uses a placeholder model. To use the actual Unitree G1:
1. Obtain the G1 USD model
2. Place it in `assets/robots/`
3. Update the path in `scripts/simulation.py`

### Performance is slow

**Solution**:
1. Close other GPU-intensive applications
2. Reduce physics timestep in the simulation
3. Lower the viewport rendering quality

## Next Steps

Once the simulation is running:

1. **Modify Parameters**: Edit `config/scene_config.yaml` to change object positions
2. **Adjust Control**: Tweak `config/robot_config.yaml` for different behaviors
3. **Extend Functionality**: Add new features in the Python scripts
4. **Add Assets**: Place custom 3D models in the `assets/` directory

## Getting Help

- Check the main [README.md](README.md) for detailed documentation
- Review the [assets/README.md](assets/README.md) for asset information
- Open an issue on GitHub if you encounter problems

## Development Tips

- Use VS Code with GitHub Copilot for best experience
- Enable Python IntelliSense for Isaac Sim modules
- Keep the Isaac Sim documentation handy: https://docs.omniverse.nvidia.com/isaacsim/

Happy simulating! 🤖🍎
