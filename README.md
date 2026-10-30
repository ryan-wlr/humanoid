# Isaac Sim Unitree G1 Fruit Sorting

This project builds an Isaac Sim scene in which a Unitree G1 walks to a desk in
the Nova Carter warehouse, picks up an apple with its right hand, and places it
in a matching bin. The table also contains orange, banana, and lemon sorting
targets with matching bins. The animation is generated from the G1's
articulated joints, including inverse kinematics for the right arm.

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
and G1 assets, places the desk, fruit, and bins, saves the assembled stage, and
uses `scripts/g1_pickup_anim.py` to author the walking, reach, grasp, lift,
placement, turn, and departure motion.

## GR00T and Fruit Sorting

For a step-by-step guide to the deterministic simulation, GR00T N1.5 download,
and the work required before a G1 policy can control the scene, see
[Fruit Sorting with GR00T](docs/groot_fruit_sorting.md). The included demo is a
safe visual baseline: only the apple is animated into its red bin. A model must
be post-trained and validated for the G1 embodiment before it controls the
other fruit.

## Interfaces and How to Run Them with GR00T

All Isaac Sim interfaces are Windows `.cmd` launchers in `scripts/`; GR00T runs
separately in Ubuntu WSL (Python 3.10), never inside `C:\isaacsim`.

| Interface | Command | Purpose |
| --- | --- | --- |
| Isaac Sim GUI | `scripts\run_nova_carter_desk_apple_ui.cmd` | Open the scene; press **Play** to watch the G1 pick the apple. |
| Headless scene | `scripts\run_nova_carter_desk_apple.cmd` | Build and save the stage without a window. |
| Video render | `scripts\make_nova_carter_desk_apple_video.cmd` | Render `docs/output/nova_carter_desk_apple.mp4`. |
| Demo recorder | `scripts\record_g1_apple_sorting_demo.cmd` | Export `output/g1_apple_to_apple_bin_raw_demo.json` and `.mp4` (joint states, actions, poses, task text, video). |
| Scene validator | `kit.exe isaacsim.exp.full.kit --no-window --exec scripts\validate_fruit_sorting_scene.py` | Check the exported USD (bins expose `fruit_sorting:fruit` and `fruit_sorting:drop_position`). |
| LeRobot converter | `python scripts\convert_g1_raw_demo_to_lerobot.py --raw <json> --video <mp4> --output <dir>` | Convert the raw demo to a LeRobot-style dataset for GR00T post-training. |
| GR00T inference server | `python scripts/inference_service.py --server --model-path <g1-checkpoint> --embodiment-tag new_embodiment --data-config unitree_g1 --denoising-steps 4` (WSL) | Serve actions to the simulator. |

### Workflow with GR00T

1. **Simulate**: run the UI launcher and confirm the scene plays.
2. **Record**: run `scripts\record_g1_apple_sorting_demo.cmd`.
3. **Convert**: run the LeRobot converter on the JSON and MP4 in `output/`.
4. **Install GR00T N1.5** in WSL (`git clone --branch n1d5
   https://github.com/NVIDIA/Isaac-GR00T.git`, then `pip install -e '.[base]'`)
   and download `nvidia/GR00T-N1.5-3B` after accepting its Hugging Face
   license.
5. **Post-train** on G1 demonstrations (varied fruit and bin positions).
6. **Serve** the post-trained checkpoint with the inference command above. The
   base checkpoint has GR-1 metadata and rejects `new_embodiment`.
7. **Connect** through the ROS 2 bridge (`docs/ros2_ws/`): cameras and G1
   state go to the GR00T service, and actions pass through a safety layer
   that clamps joint, velocity, and workspace limits before reaching the arm.

The included demo is simulation-only; never connect it to a real G1. Full
details are in [Fruit Sorting with GR00T](docs/groot_fruit_sorting.md).

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
