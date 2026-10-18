# Isaac Sim Unitree G1 Apple Pickup

This project builds an Isaac Sim scene in which a Unitree G1 walks to a desk in
the Nova Carter warehouse, picks up an apple with its right hand, and walks
away carrying it. The animation is generated from the G1's articulated joints,
including inverse kinematics for the right arm.

## Demo

[Watch the pickup animation on YouTube](https://www.youtube.com/watch?v=Z3F4pRSmpHE).

[Download the rendered pickup animation](docs/output/nova_carter_desk_apple.mp4).

## Prerequisites

- NVIDIA Isaac Sim, with the compatible Nova Carter warehouse, Unitree G1, and
  apple assets available through Nucleus or the Isaac Sim asset root.
- Windows, for the included `.cmd` launchers.
- A local Nova Carter stage at
  `C:\Users\<your-user>\OneDrive\Documents\isaac_world\nova_carter.usd`, or a
  reachable Nova Carter warehouse asset.

The launchers default to `C:\isaacsim`. Update `ISAAC_SIM_DIR`,
`SCRIPT_PATH`, and `NOVA_CARTER_USD` in the relevant launcher if your paths
differ.

## Run the Nova Carter Pickup Scene

Choose the launcher that matches how you want to use the scene:

- `scripts/run_nova_carter_desk_apple_ui.cmd` opens Isaac Sim with the scene
  and timeline available for inspection.
- `scripts/run_nova_carter_desk_apple.cmd` runs the scene headlessly and exits
  when setup is complete.
- `scripts/make_nova_carter_desk_apple_video.cmd` renders the animation to
  `docs/output/nova_carter_desk_apple.mp4`.

The scene script, `scripts/nova_carter_desk_apple.py`, discovers the warehouse
and G1 assets, places the desk and apple, saves the assembled stage, and uses
`scripts/g1_pickup_anim.py` to author the walking, reach, grasp, lift, turn,
and departure motion.

## Other Scripts

- `scripts/unitree_pickup_apple.py` is the original simple warehouse pickup
  example.
- `scripts/script_editor_load_world_and_add_desk_apple.py` loads a saved world
  and adds a desk and apple from the Isaac Sim Script Editor.
- `scripts/find_nova_assets.py` and `scripts/list_scenario_usd.py` are
  diagnostics for locating available Isaac Sim assets.

## Project Structure

- `scripts/` - Isaac Sim scene, animation, launcher, and asset-discovery
  scripts.
- `docs/output/` - the rendered MP4 and exported USD scene.
- `docs/ros2_ws/` - setup notes for an Isaac Sim ROS 2 workspace.

For Isaac Sim installation and asset setup, see the
[Isaac Sim documentation](https://docs.omniverse.nvidia.com/isaacsim/latest/).
