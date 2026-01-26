@echo off
setlocal
cd /d %~dp0

REM Spawn Unitree G1 into a kitchen-like environment (best-effort).
REM This uses the existing G1 autoload script, but switches the stage preset to "kitchen".

set UNITREE_STAGE_PRESET=kitchen

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows\start_everything_windows.ps1" -AutoLoadUnitreeG1 %*
exit /b %errorlevel%
