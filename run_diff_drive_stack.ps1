# Launch the full ROS 2 + Gazebo diff_drive stack inside WSL.
# Usage (PowerShell): .\run_diff_drive_stack.ps1
# Usage (Git Bash):   powershell.exe -ExecutionPolicy Bypass -File ./run_diff_drive_stack.ps1

$cmd = 'exec /mnt/c/Users/ryan_/run_diff_drive_stack.sh --force-x11 --reset-gui'

# Run inside WSL; the bash script sources /opt/ros/jazzy and sets D3D12 vars.
& wsl.exe -e bash -lc $cmd
exit $LASTEXITCODE
