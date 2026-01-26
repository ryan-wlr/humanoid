@echo off
setlocal
cd /d %~dp0

REM One-shot: Launch Isaac Sim (Full) with ROS 2 bridge + black-screen fix,
REM auto-spawn Unitree G1 on a ground plane, and hit Play.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows\start_everything_windows.ps1" -FixBlackViewport -AutoLoadUnitreeG1 %*
exit /b %errorlevel%
