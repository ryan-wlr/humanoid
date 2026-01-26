@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM One-shot: Launch Isaac Sim (Full) with black-screen fix,
REM load the ROS2 warehouse scene, spawn Unitree G1, create a table + apple,
REM and (best-effort) put the apple in the robot's hand.

set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%setup_windows\start_everything_windows.ps1" -FixBlackViewport -AutoLoadUnitreeG1WarehouseApplePick %*
exit /b %errorlevel%
