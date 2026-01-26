#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f /etc/os-release ]]; then
  echo "ERROR: This must be run inside WSL Ubuntu." >&2
  exit 1
fi

. /etc/os-release

echo "Detected: ${PRETTY_NAME:-unknown}"

if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "WARNING: Expected Ubuntu in WSL." >&2
fi

if [[ "${VERSION_ID:-}" != "24.04" ]]; then
  echo "WARNING: This WSL path assumes Ubuntu 24.04 (ROS 2 Jazzy)." >&2
fi

echo "WSL check OK."