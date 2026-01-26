# g1_nl_commands

Minimal ROS 2 node that turns natural-language commands (e.g. "pick up apple") into a JSON "task plan" message.

## Topics

- Input: `/nl_command` (`std_msgs/String`)
- Output: `/g1/task_plan` (`std_msgs/String`, JSON)

Example output JSON:

```json
{"intent":"pick","args":{"object":"apple"}}
```

## Run

In your ROS 2 environment (WSL is fine):

```bash
cd ~/Documents/github/ros2_ws
colcon build --symlink-install
. install/setup.bash

ros2 run g1_nl_commands nl_command_router
```

Send a command:

```bash
ros2 run g1_nl_commands nl_command_tester "pick up apple"
```

Listen for task plans:

```bash
ros2 topic echo /g1/task_plan --no-daemon
```

If you want a one-shot smoke test (router + publish + echo) from Windows, run:

```powershell
wsl.exe -d Ubuntu-24.04 -- bash -lc "bash /mnt/c/Users/ryan_/Documents/github/ros2_ws/setup_wsl/96_test_nl_commands.sh pick up apple"
```

## Hooking to a real executor

This package only produces plans. To actually *pick up an apple*, you typically also need:

- Perception: detect/track an "apple" (RGB-D + pose estimation)
- Grasping: choose a grasp pose + plan approach
- Motion control: whole-body IK + collision-aware planning

The plan format is intentionally simple so you can feed it into:
- a rule-based skill executor
- MoveIt 2 pick/place
- an Isaac Sim / OmniGraph action graph
- an LLM-based planner that maps intents to skills
