@echo off
setlocal
cd /d %~dp0

REM Downloads the official Unitree G1 USD from Unitree's GitHub (unitree_model)
REM into assets/unitree_g1/vendor/, then launches Isaac Sim and auto-spawns the robot.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows\download_unitree_g1_from_unitree_model.ps1" %*
if not "%errorlevel%"=="0" exit /b %errorlevel%

call "%~dp0run_unitree_g1_windows.cmd" %*
exit /b %errorlevel%
