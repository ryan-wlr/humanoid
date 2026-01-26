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

if [[ "${VERSION_ID:-}" != "22.04" ]]; then
  echo "ERROR: This setup targets Ubuntu 22.04 (ROS 2 Humble). Detected VERSION_ID=${VERSION_ID:-unknown}." >&2
  echo "Start the correct distro from Windows PowerShell:" >&2
  echo "  wsl -l -v" >&2
  echo "  wsl -d Ubuntu-22.04" >&2
  exit 1
fi

echo "WSL check OK."