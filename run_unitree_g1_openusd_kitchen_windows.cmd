@echo off
setlocal
cd /d %~dp0

REM Download + launch OpenUSD Kitchen Set, then spawn Unitree G1 into it.
REM Optional flags you can pass through:
REM   -FixBlackViewport -ResetKitUserConfig -ForceDownload

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows\run_unitree_g1_openusd_kitchen_windows.ps1" %*
exit /b %errorlevel%
