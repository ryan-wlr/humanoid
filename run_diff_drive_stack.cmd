@echo off
setlocal

REM Launch the full ROS 2 + Gazebo diff_drive stack inside WSL.
REM This avoids trying to run Linux scripts from Git Bash / Windows paths.

wsl.exe -e bash -lc "exec /mnt/c/Users/ryan_/run_diff_drive_stack.sh --force-x11 --reset-gui"

endlocal
