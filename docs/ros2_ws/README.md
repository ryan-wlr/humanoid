# ROS 2 Workspace for Isaac Sim ROS Bridge

This workspace is for integrating Isaac Sim with ROS 2 using the ROS bridge option. Place your ROS 2 packages in the `src/` directory.

## Usage

1. Source your ROS 2 environment:
   ```sh
   source /opt/ros/<ros-distro>/setup.bash
   ```
2. Build the workspace:
   ```sh
   colcon build
   ```
3. Source the workspace:
   ```sh
   source install/setup.bash
   ```
4. Add or clone ROS 2 packages into `src/` as needed.

---

For more information, see the Isaac Sim ROS bridge documentation:
https://docs.omniverse.nvidia.com/isaacsim/latest/ros2_tutorials.html
