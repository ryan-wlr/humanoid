#!/usr/bin/env bash
set -eo pipefail

echo "--- process hints (first 50) ---"
ps -ef | grep -E 'ros2|ros_gz|gz|gazebo|rviz|controller|spawn|diff_drive' | grep -v grep | head -n 50 || true

echo "--- tail diff_drive stack log (~/.ros2ws_diff_drive_stack.log) ---"
tail -n 120 "$HOME/.ros2ws_diff_drive_stack.log" 2>/dev/null || echo "(no log file)"

echo "--- tail discovery server log (~/.ros2ws_fastdds_11812.log) ---"
tail -n 80 "$HOME/.ros2ws_fastdds_11812.log" 2>/dev/null || echo "(no log file)"
