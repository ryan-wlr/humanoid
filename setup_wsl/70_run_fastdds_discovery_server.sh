#!/usr/bin/env bash
set -euo pipefail

# Runs a Fast DDS Discovery Server (unicast discovery) for cases where multicast discovery is blocked.
# Requires Fast DDS CLI tools package.

if ! command -v fastdds >/dev/null 2>&1; then
  echo "Installing Fast DDS discovery server tools..." 
  sudo apt-get update
  sudo apt-get install -y fastdds-tools
fi

PORT="${1:-11811}"

# Check if UDP port is already bound
if command -v ss >/dev/null 2>&1; then
  if ss -lun | awk '{print $5}' | grep -qE ":[[:space:]]*${PORT}$|:${PORT}$"; then
    echo "ERROR: UDP port ${PORT} is already in use." >&2
    echo "Pick a different port, e.g.:" >&2
    echo "  ./setup_wsl/70_run_fastdds_discovery_server.sh 11812" >&2
    echo >&2
    echo "If you want to see what is using it:" >&2
    echo "  ss -lunp | grep :${PORT} || ss -lun | grep :${PORT}" >&2
    exit 1
  fi
fi

echo "Starting Fast DDS Discovery Server on UDP port ${PORT}"
echo "Leave this terminal running."
echo
echo "Then set on BOTH sides (WSL and Windows/Isaac Sim environment):"
echo "  ROS_DISCOVERY_SERVER=<server_ip>:${PORT}"
echo
echo "WSL server IP hint (pick the one reachable from Windows):"
ip -4 addr | grep -E "inet " || true

echo
echo "Running: fastdds discovery -i 0 -p ${PORT}"
fastdds discovery -i 0 -p "${PORT}"