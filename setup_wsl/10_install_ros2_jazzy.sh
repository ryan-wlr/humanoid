#!/usr/bin/env bash
set -euo pipefail

# Installs ROS 2 Jazzy on Ubuntu 24.04 (WSL).

if [[ $EUID -eq 0 ]]; then
  echo "Please run as a normal user (script uses sudo)." >&2
  exit 1
fi

bash setup_wsl/00_wsl_check.sh

echo "Updating apt (this will fail if your APT sources are corrupted)..."
if ! sudo apt-get update; then
  echo >&2
  echo "ERROR: apt-get update failed." >&2
  echo "A common cause is accidentally pasting a 'BEGIN PGP PUBLIC KEY BLOCK' into an APT sources file." >&2
  echo "To detect/repair that, run:" >&2
  echo "  bash setup_wsl/05_repair_apt_sources.sh" >&2
  exit 1
fi

sudo apt-get install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

sudo apt-get install -y \
  software-properties-common \
  curl \
  ca-certificates \
  gnupg

sudo add-apt-repository -y universe

sudo install -m 0755 -d /etc/apt/keyrings
if [[ ! -f /etc/apt/keyrings/ros-archive-keyring.gpg ]]; then
  tmpkey="$(mktemp)"
  curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o "${tmpkey}"
  sudo gpg --dearmor -o /etc/apt/keyrings/ros-archive-keyring.gpg "${tmpkey}"
  rm -f "${tmpkey}"
fi

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null

sudo apt-get update
sudo apt-get install -y ros-jazzy-desktop python3-colcon-common-extensions python3-rosdep

sudo rosdep init || true
rosdep update

echo
echo "ROS 2 Jazzy installed in WSL."
echo "Run: source /opt/ros/jazzy/setup.bash"