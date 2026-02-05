# Assets Directory

This directory is intended for 3D models and assets used in the simulation.

## Required Assets

### 1. Unitree G1 Robot Model

The Unitree G1 humanoid robot model should be placed here in USD format.

**Options to obtain the model:**

- **From Unitree Robotics**: Contact Unitree for official robot models
- **From Isaac Sim Asset Library**: Check if available in NVIDIA's asset store
- **Custom URDF to USD Conversion**: Convert Unitree's URDF to USD format

**Expected file**: `g1_robot.usd` or `g1_robot/`

### 2. Apple Model (Optional)

The simulation creates a simple sphere for the apple, but you can use a detailed 3D model.

**File formats supported**: `.usd`, `.usda`, `.usdc`

### 3. Desk Model (Optional)

The simulation creates a simple box for the desk, but you can use a detailed 3D model.

## File Structure

```
assets/
├── robots/
│   └── unitree_g1/
│       ├── g1.usd              # Main robot file
│       ├── meshes/             # Visual meshes
│       └── textures/           # Textures
├── objects/
│   ├── apple.usd              # Apple model
│   └── desk.usd               # Desk model
└── README.md                   # This file
```

## Using Assets in Code

To use custom assets, update the paths in `scripts/simulation.py`:

```python
# Load custom robot model
robot_usd_path = "assets/robots/unitree_g1/g1.usd"
add_reference_to_stage(usd_path=robot_usd_path, prim_path="/World/G1")

# Load custom apple model
apple_usd_path = "assets/objects/apple.usd"
add_reference_to_stage(usd_path=apple_usd_path, prim_path="/World/Apple")
```

## Asset Creation

### Converting URDF to USD

If you have a URDF file, convert it to USD using Isaac Sim's converter:

```bash
# From Isaac Sim Python
from omni.isaac.urdf import _urdf
urdf_interface = _urdf.acquire_urdf_interface()
urdf_interface.parse_urdf("path/to/robot.urdf", "path/to/output.usd")
```

### Creating Simple Objects

For testing, you can create simple geometric objects in the simulation code (as currently implemented).

## Notes

- The current implementation uses procedurally generated objects
- Custom USD assets will provide better visual quality and physics accuracy
- Make sure asset scales match the simulation's unit system (meters)
- Test collision geometry separately before using in manipulation tasks

## Resources

- [NVIDIA Isaac Sim Asset Documentation](https://docs.omniverse.nvidia.com/app_isaacsim/app_isaacsim/tutorial_asset.html)
- [USD Format Specification](https://graphics.pixar.com/usd/docs/index.html)
- [Unitree Robotics Official Website](https://www.unitree.com/)
