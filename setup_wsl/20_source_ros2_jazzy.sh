#!/usr/bin/env bash
set -euo pipefail

# Sources ROS 2 Jazzy and applies a couple of common environment defaults.

if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  echo "ERROR: /opt/ros/jazzy/setup.bash not found. Is ROS 2 Jazzy installed?" >&2
  exit 1
fi

# ROS setup scripts sometimes reference optional env vars that may be unset.
# With `set -u`, that can hard-fail (e.g., AMENT_TRACE_SETUP_FILES).
had_nounset=0
if [[ "${-}" == *u* ]]; then
  had_nounset=1
  set +u
fi

# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash

if [[ "$had_nounset" -eq 1 ]]; then
  set -u
fi

# Keep ROS 2 domain consistent between Isaac Sim side and WSL side.
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"

# Isaac Sim ROS 2 bridge commonly uses Fast DDS; default to it unless user already chose.
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"

# Optional: force UDP-only builtin transport to avoid SHM issues across Windows<->WSL.
if [[ -n "${FASTDDS_BUILTIN_TRANSPORTS:-}" ]]; then
  echo "FASTDDS_BUILTIN_TRANSPORTS=$FASTDDS_BUILTIN_TRANSPORTS"
fi

echo "ROS_DISTRO=$ROS_DISTRO"
echo "ROS_VERSION=$ROS_VERSION"
echo "ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
echo "RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"