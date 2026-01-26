#!/usr/bin/env bash
set -euo pipefail

# Installs NVIDIA Container Toolkit and configures Docker to use it.
# Requires NVIDIA driver already installed on the host.

if [[ $EUID -eq 0 ]]; then
  echo "Please run as a normal user (script will use sudo when needed)." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings

# Add NVIDIA container toolkit repo
if [[ ! -f /etc/apt/keyrings/nvidia-container-toolkit.gpg ]]; then
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
    | sudo gpg --dearmor -o /etc/apt/keyrings/nvidia-container-toolkit.gpg
  sudo chmod a+r /etc/apt/keyrings/nvidia-container-toolkit.gpg
fi

distribution=$(. /etc/os-release;echo ${ID}${VERSION_ID})

curl -fsSL https://nvidia.github.io/libnvidia-container/${distribution}/libnvidia-container.list \
  | sed 's#deb https://#deb [signed-by=/etc/apt/keyrings/nvidia-container-toolkit.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

echo
echo "NVIDIA Container Toolkit installed and Docker restarted."
echo "Quick test: docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi"