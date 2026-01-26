# humanoid

Unitree G1 in Isaac Sim + ROS 2 tooling (Windows + WSL). Includes one-click launchers and demo scripts (e.g. warehouse + table/apple pick).

## Repo layout
- `setup_wsl/`: WSL scripts to install/configure ROS 2 and Fast DDS discovery server
- `setup_windows/`: Windows PowerShell helpers (firewall rules, Isaac Sim launch, diagnostics, exec scripts)
- `docker/`: container image definitions and compose files
- Top-level `run_*.cmd` / `run_*.ps1` / `run_*.sh`: convenience entrypoints

## Typical usage
- Follow the setup guide: `SETUP_WINDOWS_ISAACSIM_WSL_ROS2.md`
- Launch a demo from Command Prompt, for example:
  - `run_unitree_g1_warehouse_apple_pick_windows.cmd`

## Notes
This is a standard ROS 2/colcon workspace; build artifacts are ignored via `.gitignore` (`build/`, `install/`, `log/`).
