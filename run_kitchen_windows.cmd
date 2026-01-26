@echo off
setlocal
cd /d %~dp0

REM Launch Isaac Sim and auto-load a kitchen environment (best-effort).
REM Optional override:
REM   set KITCHEN_STAGE_USD=<local path or omniverse:// url>

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows\launch_isaac_sim_with_ros2.ps1" ^
  -Mode kit ^
  -AppKit "isaacsim.exp.full.kit" ^
  -RosDistro jazzy ^
  -DiscoveryServer "" ^
  -FixBlackViewport ^
  -ResetKitUserConfig ^
  -ExecScript "%~dp0setup_windows\auto_load_kitchen.py" ^
  -Detach

exit /b %errorlevel%
