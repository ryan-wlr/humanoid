#!/usr/bin/env bash
set -eo pipefail

DOMAIN_ID="${1:-0}"
DISCOVERY_SERVER="${2:-127.0.0.1:11812}"
ROS_DISTRO="${3:-jazzy}"

# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"

export ROS_DOMAIN_ID="${DOMAIN_ID}"
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
export ROS_DISCOVERY_SERVER="${DISCOVERY_SERVER}"

echo "--- ROS env ---"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
echo "ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER}"
echo "ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY}"
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}"
echo "FASTDDS_BUILTIN_TRANSPORTS=${FASTDDS_BUILTIN_TRANSPORTS}"

echo "--- fast-discovery-server ps ---"
ps -ef | grep -E 'fast-discovery-server|fastdds' | grep -v grep || true

echo "--- ros2 daemon restart (best-effort) ---"
ros2 daemon stop >/dev/null 2>&1 || true
timeout -k 1s 5s ros2 daemon start >/dev/null 2>&1 || true

echo "--- ros2 node list ---"
timeout -k 1s 8s ros2 node list || echo "(node list timed out)"

echo "--- ros2 topic list (first 200) ---"
timeout -k 1s 8s ros2 topic list -t | head -n 200 || echo "(topic list timed out)"
