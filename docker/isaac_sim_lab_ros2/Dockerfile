# syntax=docker/dockerfile:1

ARG ISAAC_SIM_BASE_IMAGE
FROM ${ISAAC_SIM_BASE_IMAGE}

SHELL ["/bin/bash", "-lc"]

# --- Base utilities ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    gnupg \
    lsb-release \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# --- ROS 2 Humble (inside container) ---
# Note: Keeping ROS 2 inside the same container is the fastest "single container" workflow.
RUN apt-get update && apt-get install -y --no-install-recommends locales && \
    locale-gen en_US en_US.UTF-8 && \
    update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*
ENV LANG=en_US.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository -y universe && \
    rm -rf /var/lib/apt/lists/*

RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
      | gpg --dearmor -o /etc/apt/keyrings/ros-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
      > /etc/apt/sources.list.d/ros2.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-ros-base \
    python3-colcon-common-extensions \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

RUN rosdep init || true && rosdep update

# --- Isaac Lab ---
# Install Isaac Lab from source. Adjust branch/tag as needed.
WORKDIR /opt
RUN git clone https://github.com/isaac-sim/IsaacLab.git isaaclab
WORKDIR /opt/isaaclab

# Isaac Lab uses its own Python tooling; keep it simple and use pip editable.
RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -e .

# Convenience: source ROS 2 by default
RUN echo "source /opt/ros/humble/setup.bash" >> /etc/bash.bashrc

WORKDIR /workspace
