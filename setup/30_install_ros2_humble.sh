#!/usr/bin/env bash
set -euo pipefail

# Installs ROS 2 Humble on Ubuntu 22.04 (host install).

if [[ $EUID -eq 0 ]]; then
  echo "Please run as a normal user (script will use sudo when needed)." >&2
  exit 1
fi

sudo apt-get update
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
  curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    | sudo gpg --dearmor -o /etc/apt/keyrings/ros-archive-keyring.gpg
fi

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null

sudo apt-get update
sudo apt-get install -y ros-humble-desktop python3-colcon-common-extensions python3-rosdep

sudo rosdep init || true
rosdep update

echo
echo "ROS 2 Humble installed."
echo "Add to your shell: source /opt/ros/humble/setup.bash"