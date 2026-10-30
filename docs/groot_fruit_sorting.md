# G1 Fruit Sorting: Beginner Guide

This project contains a safe, visual first step toward a GR00T-controlled
fruit sorter. It is a simulator demonstration only. Do **not** connect it to a
real G1 robot.

The demo begins with an apple, orange, banana, and lemon on a table. Four open
bins identify the fruit destinations by color:

| Fruit | Bin color |
| --- | --- |
| Apple | red |
| Orange | orange |
| Banana | yellow |
| Lemon | yellow |

The supplied baseline animation picks up the apple and puts it in the red
apple bin. The remaining fruit is deliberately left in place: this is the
expected behavior until a G1-specific policy has been trained and validated.

## Part 1: Run the scene

1. Make sure Isaac Sim is closed.
2. In File Explorer, open the repository's `scripts` folder.
3. Double-click `run_nova_carter_desk_apple_ui.cmd`.
4. Wait for Isaac Sim to open. This can take several minutes on the first
   launch.
5. Press the **Play** button at the bottom of Isaac Sim.
6. Watch the G1 walk to the table, pick up the apple, and release it in the
   red bin.

If the scene does not load, edit the three paths at the top of
`run_nova_carter_desk_apple_ui.cmd`: `ISAAC_SIM_DIR`, `SCRIPT_PATH`, and
`NOVA_CARTER_USD`.

The generated USD is saved under
`C:\Users\<your-user>\OneDrive\Documents\isaac_world\nova_carter_desk_apple.usd`.
The bins expose `fruit_sorting:fruit` and `fruit_sorting:drop_position` USD
attributes, so code can find the correct destination without relying on a
hard-coded location.

To check the exported scene, open a Command Prompt and run:

```bat
set SCENE_PATH=C:\Users\<your-user>\OneDrive\Documents\isaac_world\nova_carter_desk_apple.usd
C:\isaacsim\kit\kit.exe C:\isaacsim\apps\isaacsim.exp.full.kit --no-window --exec C:\Users\<your-user>\Documents\github\humanoid\scripts\validate_fruit_sorting_scene.py
```

## Part 2: What GR00T does and does not do

GR00T N1.5 can use camera images, a language instruction, and robot state to
produce a sequence of actions. It is **not** a general-purpose controller that
can safely drive any G1 out of the box. Before using it for this scene, you
must supply:

1. A Unitree G1 embodiment definition: exact joint ordering, state
   normalization, action normalization, camera names, and control frequency.
2. Demonstrations for the G1 sorting task, collected in simulation and stored
   in the LeRobot-compatible schema required by GR00T.
3. A post-trained checkpoint evaluated against randomized fruit positions,
   lighting, bin placement, and physics settings.
4. A safety layer that clamps targets to the G1 joint, velocity, workspace,
   and collision limits.

Until these four requirements are satisfied, use the included deterministic
animation only. Never send an unvalidated VLA action vector directly to an
articulated humanoid.

## Part 3: Download and start GR00T N1.5 in WSL

Do this in Ubuntu WSL, not from Isaac Sim's Python installation. NVIDIA tested
N1.5 on Ubuntu with Python 3.10 and NVIDIA GPUs. The checkpoint is
non-commercial; create a Hugging Face account and accept the NVIDIA model
license on the model page before downloading.

Open an Ubuntu WSL terminal and run:

```bash
cd ~
git clone --branch n1d5 https://github.com/NVIDIA/Isaac-GR00T.git
cd Isaac-GR00T
conda create -n gr00t python=3.10
conda activate gr00t
pip install --upgrade setuptools
pip install -e '.[base]'
```

For an RTX 50-series Blackwell GPU, install a CUDA 12.8-compatible PyTorch
build, then compile FlashAttention for `sm_120`. Build only the architecture
installed in your computer to avoid unnecessary compilation and memory use:

```bash
pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu128
git clone https://github.com/Dao-AILab/flash-attention.git ~/flash-attention
cd ~/flash-attention
git checkout v2.8.3
export CUDA_HOME=/usr/local/cuda-12.8
export FLASH_ATTN_CUDA_ARCHS=120
export MAX_JOBS=1
export NVCC_THREADS=1
pip install --no-build-isolation .
```

Verify the installation:

```bash
python -c "import flash_attn, torch; print(flash_attn.__version__); print(torch.cuda.get_device_capability())"
```

Download the checkpoint after accepting its Hugging Face model license:

```bash
hf download nvidia/GR00T-N1.5-3B --local-dir ~/models/GR00T-N1.5-3B
```

Do not install these dependencies into `C:\isaacsim`; its Python is 3.11 and
is intentionally separate.

## Part 4: Connect it only after post-training

The base `GR00T-N1.5-3B` checkpoint contains GR-1 normalization metadata, not
metadata for a new Unitree G1 embodiment. The inference service correctly
rejects `--embodiment-tag new_embodiment` until post-training creates a
checkpoint with matching G1 state/action statistics. Do not substitute the
GR-1 metadata or send the base model's actions to the G1.

After producing a post-trained G1 checkpoint, start its service from WSL:

```bash
cd ~/Isaac-GR00T
python scripts/inference_service.py --server \
  --model-path /path/to/post-trained-g1-checkpoint \
  --embodiment-tag new_embodiment \
  --data-config unitree_g1 \
  --denoising-steps 4
```

The intended data route is:

```text
Isaac Sim cameras + G1 state -> ROS 2 bridge -> G1 observation adapter
-> GR00T inference service -> safety/action adapter -> Isaac arm controller
```

Use two RGB cameras: an external table view and a right-wrist view. Resize
each image to 224 by 224 only in the observation adapter. Keep a time-stamped
copy of every image, joint-state vector, instruction, action chunk, and
safety-clamp event. That record is needed to reproduce failures and build the
fine-tuning dataset.

Start with only the right arm and hand enabled. Keep the existing walking and
balance behavior fixed. Enable one action chunk at a time, stop if the safety
layer clips an action, and reset the simulation after every failed grasp.

## Part 5: Teach the sorter

1. Use the scripted apple pick as the first successful demonstration. Run
   `scripts\record_g1_apple_sorting_demo.cmd` to export
   `output\g1_apple_to_apple_bin_raw_demo.json`.
2. Make copies with apples moved to many table locations.
3. Add one fruit type at a time: orange, then banana, then lemon.
4. For every fruit, vary its position and the matching bin's position.
5. Record successful and failed episodes separately.
6. Train/post-train on the successful demonstrations.
7. Test on fruit and bin positions never used during training.
8. Only then let the policy select between all four bins.

Success means the object is inside the matching bin after the gripper opens;
it does not merely mean that the G1 touched the fruit.

The raw export contains ordered named joint positions, next-frame action
targets, base pose, apple pose, bin target, and the task text. It is
deliberately not a GR00T training dataset yet: each episode needs synchronized
camera video and a validated mapping from the simulator's G1 joint names to
the `unitree_g1` state/action fields before conversion to LeRobot format.
