# Isaac Sim + Isaac Lab + ROS 2 (Ubuntu 22.04 + Docker)

This repo now includes scripts to set up a **reliable** Isaac Sim + Isaac Lab + ROS 2 environment on **native Ubuntu 22.04** using Docker.

> Note: This is **not** recommended in WSL for Isaac Sim GUI. Do this on a machine booted into Ubuntu 22.04 (dual boot, separate SSD, etc.).

## 0) Prereqs (5 minutes)

1. Install Ubuntu 22.04 *natively*.
2. Install an NVIDIA driver on Ubuntu and reboot.
3. Confirm GPU works:

```bash
nvidia-smi
```

If `nvidia-smi` does not work, stop here and fix the driver first.

## 1) One-time host setup (Docker + NVIDIA toolkit + ROS 2)

From the root of this workspace on Ubuntu:

```bash
cd /path/to/ros2_ws

# one-time: make scripts executable
bash setup/chmod_all.sh

bash setup/00_prereqs_check.sh
bash setup/10_install_docker.sh
bash setup/20_install_nvidia_container_toolkit.sh

# optional but recommended if you also want ROS 2 on the host
bash setup/30_install_ros2_humble.sh
```

After docker install, either log out/in (for the `docker` group) or run:

```bash
newgrp docker
```

## 2) Pick your Isaac Sim container tag

Isaac Sim container images are hosted on **NGC** (`nvcr.io`). You’ll need an NVIDIA account and to accept the Isaac Sim container EULA in NGC.

1. Log in:

```bash
docker login nvcr.io
```

2. Choose a base image tag and export it (example placeholder below):

```bash
export ISAAC_SIM_BASE_IMAGE="nvcr.io/nvidia/isaac-sim:<PUT_TAG_HERE>"
```

If you don’t know the tag yet, run:

```bash
bash setup/35_help_find_isaac_sim_tag.sh
```

(That script prints where to look and what to copy/paste.)

## 3) Build the combined image (Isaac Sim + ROS 2 + Isaac Lab)

```bash
bash setup/40_build_image.sh
```

## 4) Run Isaac Sim container

### GUI mode (X11)

On Ubuntu with Xorg/X11:

```bash
bash setup/50_run_gui.sh

# enter the container
bash setup/60_enter_container.sh
```

### Headless mode (no GUI)

```bash
bash setup/55_run_headless.sh
```

## 5) Verify ROS 2 bridge

In a separate terminal on the **host** (or in your ROS 2 container), verify topics:

```bash
source /opt/ros/humble/setup.bash
ros2 topic list
```

## Common issues

- **Black window / Vulkan errors**: usually driver/Vulkan mismatch. Confirm `nvidia-smi` works and you’re on a supported NVIDIA driver.
- **No ROS 2 topics**: ensure DDS matches and `ROS_DOMAIN_ID` is consistent between Isaac Sim and your ROS 2 side.

## Next step

Tell me:
- your GPU model and driver version (`nvidia-smi` output),
- whether you need GUI or headless,
- your ROS 2 distro preference (Humble recommended for Ubuntu 22.04),

…and I’ll tailor the `docker-compose` env vars to your exact setup.
