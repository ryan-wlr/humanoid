#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${ISAAC_SIM_BASE_IMAGE:-}" ]]; then
  echo "ERROR: ISAAC_SIM_BASE_IMAGE is not set." >&2
  echo "Example: export ISAAC_SIM_BASE_IMAGE=nvcr.io/nvidia/isaac-sim:<TAG>" >&2
  exit 1
fi

# Basic sanity
if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker not running or you don't have permission." >&2
  echo "Try: sudo systemctl start docker && newgrp docker" >&2
  exit 1
fi

echo "Building image from base: $ISAAC_SIM_BASE_IMAGE"

docker compose -f docker-compose.ubuntu22.yml build

echo "Build complete."