#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f /opt/ros/humble/setup.bash ]]; then
  echo "ERROR: /opt/ros/humble/setup.bash not found. Is ROS 2 Humble installed?" >&2
  exit 1
fi

had_nounset=0
if [[ "${-}" == *u* ]]; then
  had_nounset=1
  set +u
fi

# shellcheck disable=SC1091
source /opt/ros/humble/setup.bash

if [[ "$had_nounset" -eq 1 ]]; then
  set -u
fi

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"

# Optional: avoid SHM across Windows<->WSL
export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-UDPv4}"

if [[ -n "${ROS_DISCOVERY_SERVER:-}" ]]; then
  echo "ROS_DISCOVERY_SERVER=$ROS_DISCOVERY_SERVER"
fi

echo "ROS_DISTRO=$ROS_DISTRO"
echo "ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
echo "RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"
echo "FASTDDS_BUILTIN_TRANSPORTS=$FASTDDS_BUILTIN_TRANSPORTS"