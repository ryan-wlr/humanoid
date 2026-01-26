#!/usr/bin/env bash
set -euo pipefail

bash setup_wsl_2204/20_source_ros2_humble.sh

if ! command -v ros2 >/dev/null 2>&1; then
	echo >&2
	echo "ERROR: 'ros2' command not found after sourcing /opt/ros/humble/setup.bash." >&2
	echo "ROS 2 Humble is likely not installed in this WSL distro." >&2
	echo "Run:" >&2
	echo "  bash setup_wsl_2204/10_install_ros2_humble.sh" >&2
	exit 1
fi

echo
echo "== ros2 doctor =="
ros2 doctor --report || true

echo
echo "== ros2 nodes/topics =="
ros2 node list || true
ros2 topic list || true

echo
echo "OK: ROS 2 Humble tools run."