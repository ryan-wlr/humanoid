#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${ISAAC_SIM_BASE_IMAGE:-}" ]]; then
  echo "ERROR: ISAAC_SIM_BASE_IMAGE is not set." >&2
  echo "Example: export ISAAC_SIM_BASE_IMAGE=nvcr.io/nvidia/isaac-sim:<TAG>" >&2
  exit 1
fi

# Allow local root inside container to access X server.
# You can tighten this later; this is the quickest "make it work" approach.
if command -v xhost >/dev/null 2>&1; then
  xhost +local:root >/dev/null
else
  echo "WARNING: xhost not found; install with: sudo apt-get install -y x11-xserver-utils" >&2
fi

export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# Start container

docker compose -f docker-compose.ubuntu22.yml up -d

echo
echo "Container started. Open a shell with:"
echo "  docker exec -it isaac-sim-lab-ros2 bash"
echo
echo "Inside the container, try one of these (depends on the base image layout):"
echo "  cd /isaac-sim && ./isaac-sim.sh"
echo "  cd /opt/isaac-sim && ./isaac-sim.sh"
echo
echo "If you don't know where the launcher is, run:"
echo "  find / -maxdepth 4 -type f -name '*isaac*sim*.sh' 2>/dev/null | head"