@echo off
setlocal
cd /d %~dp0

REM One-click: download OpenUSD Kitchen Set (if needed) + launch Isaac Sim + spawn Unitree G1.
REM Optional flags you can pass through:
REM   -FixBlackViewport -ResetKitUserConfig -ForceDownload -LocalhostOnly

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows\run_unitree_g1_into_kitchen_windows.ps1" %*
exit /b %errorlevel%
