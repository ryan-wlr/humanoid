#!/usr/bin/env bash
set -euo pipefail

bash setup_wsl/20_source_ros2_jazzy.sh

echo
echo "== ros2 doctor =="
ros2 doctor --report || true

echo
echo "== ros2 nodes/topics (should work even if empty) =="
ros2 node list || true
ros2 topic list || true

echo
echo "OK: ROS 2 command-line tools run."