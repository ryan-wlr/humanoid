#!/usr/bin/env bash
set -euo pipefail

echo "== Checking host OS =="
if [[ ! -f /etc/os-release ]]; then
  echo "ERROR: /etc/os-release not found." >&2
  echo "This script must be run inside an Ubuntu Linux environment (native Ubuntu 22.04 preferred)." >&2
  echo >&2
  echo "It looks like you're running in a Windows shell (e.g., Git Bash / MINGW)." >&2
  echo "Next steps:" >&2
  echo "  - If you have Ubuntu installed: open an Ubuntu terminal and re-run: bash setup/00_prereqs_check.sh" >&2
  echo "  - If you want WSL (not recommended for Isaac Sim GUI): open PowerShell and run: wsl -l -v" >&2
  echo "  - If you don't have Ubuntu yet: install Ubuntu 22.04 (dual boot or separate machine) for the best Isaac Sim experience." >&2
  exit 1
fi

. /etc/os-release

echo "Detected: ${PRETTY_NAME:-unknown}"

if [[ "${ID:-}" != "ubuntu" ]]; then
  echo "WARNING: This setup targets Ubuntu. Detected ID=${ID:-unknown}." >&2
fi

if [[ "${VERSION_ID:-}" != "22.04" ]]; then
  echo "WARNING: Recommended host is Ubuntu 22.04. Detected VERSION_ID=${VERSION_ID:-unknown}." >&2
fi

echo

echo "== Checking NVIDIA GPU =="
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi || true
else
  echo "WARNING: nvidia-smi not found. Install NVIDIA driver first." >&2
fi

echo

echo "== Checking Docker =="
if command -v docker >/dev/null 2>&1; then
  docker --version
else
  echo "Docker not installed yet (expected)." 
fi

echo

echo "OK: prereq check completed."