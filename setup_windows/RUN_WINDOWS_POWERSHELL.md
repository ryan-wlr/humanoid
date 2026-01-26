# Run Isaac Sim from VS Code (PowerShell)

Open a VS Code terminal and switch it to **PowerShell**.

## If `conda` is not recognized

VS Code terminals often start without Anaconda initialized, which makes `conda` unavailable.

This repo includes a helper that loads Conda into the current PowerShell session (and optionally activates an env).

Important: run it in-place (dot-source) so it modifies the current session:

```powershell
. .\setup_windows\ensure_conda.ps1 -EnvName base
```

If that still fails, open **Anaconda Prompt** and run `conda init powershell` once, then restart VS Code.

## 1) Set env vars (user-scope)

```powershell
cd $env:USERPROFILE\Documents\github\ros2_ws
powershell -ExecutionPolicy Bypass -File .\setup_windows\set_isaac_ros2_env_user.ps1 -DomainId 0 -DiscoveryServer "192.168.1.200:11812"
```

## 2) Launch Isaac Sim with env vars applied

Close **all** running Isaac Sim/Kit windows first (Kit can keep state/locks across runs).

```powershell
cd $env:USERPROFILE\Documents\github\ros2_ws
powershell -ExecutionPolicy Bypass -File .\setup_windows\launch_isaac_sim_with_ros2.ps1 -Mode isaac-sim.bat
```

Note: the launcher auto-enables the ROS 2 bridge extensions by default (`isaacsim.ros2.bridge` and `omni.isaac.ros2_bridge`).

If that doesn’t launch the right app, try:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows\launch_isaac_sim_with_ros2.ps1 -Mode isaac-sim.selector.bat
```

Or launch via Kit app config:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows\launch_isaac_sim_with_ros2.ps1 -Mode kit
```

If you want to disable auto-enabling extensions (not recommended while debugging):

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows\launch_isaac_sim_with_ros2.ps1 -Mode kit -EnableRos2Bridge $false
```
