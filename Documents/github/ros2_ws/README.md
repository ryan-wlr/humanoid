# Isaac Sim + ROS2 Unitree G1 Demo

This repository provides a complete Windows + WSL workspace for running Isaac Sim with ROS2 integration, including a Unitree G1 robot demo and natural-language command pipeline.

## Features
- One-click launch scripts for Isaac Sim and ROS2 bridge
- WSL setup scripts for ROS2 Jazzy and Humble
- Unitree G1 warehouse "apple pick" demo
- Natural-language command router (`g1_nl_commands`)
- Robust PowerShell and Bash automation

## Quick Start

1. **Install Prerequisites**
   - Windows 10/11
   - WSL2 (Ubuntu 24.04 recommended)
   - Isaac Sim (see NVIDIA docs)
   - Docker (optional, for container workflows)

2. **Clone the Repository**
   ```sh
   git clone https://github.com/ryan-wlr/humanoid.git
   cd humanoid
   ```

3. **WSL Setup**
   - Open WSL terminal and run:
     ```sh
     bash setup_wsl/10_install_ros2_jazzy.sh
     bash setup_wsl/30_ros2_sanity_check.sh
     ```

4. **Windows Setup**
   - Use PowerShell to run:
     ```powershell
     setup_windows\start_everything_windows.ps1 -AutoLoadUnitreeG1WarehouseApplePick -FixBlackViewport
     ```
   - Or double-click the `.cmd` wrappers for one-click launch.

5. **Demo: Unitree G1 Apple Pick**
   - Isaac Sim will launch, load the warehouse stage, spawn the Unitree G1 robot, and perform a reach-down apple pick animation.
   - Status logs are written to `setup_windows/auto_load_unitree_g1_warehouse_apple_pick.status.txt`.

## Natural-Language Command Pipeline
- ROS2 package: `src/g1_nl_commands`
- Run the router in WSL:
  ```sh
  ros2 run g1_nl_commands nl_command_router
  ros2 run g1_nl_commands nl_command_tester "pick up apple"
  ```

## Video Demo
[![YouTube Demo](https://img.youtube.com/vi/khArguGTgfQ/0.jpg)](https://www.youtube.com/watch?v=khArguGTgfQ)

Watch the full demo here: https://www.youtube.com/watch?v=khArguGTgfQ

## Troubleshooting
- If you encounter file lock or merge issues, ensure all editors and terminals are closed and retry.
- For WSL/ROS2 issues, see the setup scripts in `setup_wsl/` and `setup_wsl_2204/`.

## License
Apache-2.0
