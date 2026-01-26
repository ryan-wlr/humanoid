@echo off
setlocal
cd /d %~dp0

REM Launch Unitree G1 WITHOUT the black-viewport present override.
REM Use this if the viewport is visible but the window is flickering/flashing.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows\start_everything_windows.ps1" -AutoLoadUnitreeG1 %*
exit /b %errorlevel%
