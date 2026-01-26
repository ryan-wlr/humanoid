#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${ISAAC_SIM_BASE_IMAGE:-}" ]]; then
  echo "ERROR: ISAAC_SIM_BASE_IMAGE is not set." >&2
  echo "Example: export ISAAC_SIM_BASE_IMAGE=nvcr.io/nvidia/isaac-sim:<TAG>" >&2
  exit 1
fi

export DISPLAY="${DISPLAY:-}"
export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

# Start container

docker compose -f docker-compose.ubuntu22.yml up -d

echo
echo "Container started (headless-friendly)."
echo "Enter it with: docker exec -it isaac-sim-lab-ros2 bash"