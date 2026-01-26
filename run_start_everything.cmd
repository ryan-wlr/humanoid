@echo off
setlocal
cd /d %~dp0

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows\start_everything.ps1" %*
exit /b %errorlevel%
