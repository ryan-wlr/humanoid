#!/usr/bin/env bash
set -eo pipefail

DOMAIN_ID="${1:-0}"
DISCOVERY_SERVER="${2:-127.0.0.1:11812}"
ROS_DISTRO="${3:-jazzy}"
OUT_DIR="/mnt/c/Users/ryan_/Documents/github/ros2_ws/setup_wsl"
OUT_FILE="${OUT_DIR}/wsl_ros2_graph.txt"

mkdir -p "${OUT_DIR}" || true

# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"

export ROS_DOMAIN_ID="${DOMAIN_ID}"
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
export ROS_DISCOVERY_SERVER="${DISCOVERY_SERVER}"
export ROS2CLI_DAEMON=0

{
  echo "timestamp=$(date -Is)"
  echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
  echo "ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER}"
  echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"
  echo ""

  echo "--- ros2 node list ---"
  timeout -k 1s 8s ros2 node list || echo "(node list timed out)"
  echo ""

  echo "--- ros2 topic list -t ---"
  timeout -k 1s 8s ros2 topic list -t || echo "(topic list timed out)"
  echo ""
} >"${OUT_FILE}" 2>&1

echo "WROTE=${OUT_FILE}"
