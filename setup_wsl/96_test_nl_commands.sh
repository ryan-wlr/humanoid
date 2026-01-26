#!/usr/bin/env bash
set -eEo pipefail

# Smoke-test for the g1_nl_commands package.
# Runs entirely inside WSL (ROS 2 Jazzy assumed).

CMD_TEXT="${*:-pick up apple}"

# ROS setup scripts sometimes reference optional env vars that may be unset.
# Avoid hard failures if the caller enables nounset.
had_nounset=0
if [[ "${-}" == *u* ]]; then
  had_nounset=1
  set +u
fi

# shellcheck disable=SC1091
source /opt/ros/jazzy/setup.bash

if [[ "$had_nounset" -eq 1 ]]; then
  set -u
fi

cd /mnt/c/Users/ryan_/Documents/github/ros2_ws

# shellcheck disable=SC1091
source install/setup.bash

echo "Starting nl_command_router..." >&2
ros2 run g1_nl_commands nl_command_router &
router_pid=$!

cleanup() {
  kill "$router_pid" >/dev/null 2>&1 || true
  wait "$router_pid" >/dev/null 2>&1 || true
}
trap cleanup EXIT

sleep 0.8

echo "Subscribing to /g1/task_plan (--once)..." >&2
tmp_out="$(mktemp)"
if command -v timeout >/dev/null 2>&1; then
  timeout 10s ros2 topic echo /g1/task_plan --once --no-daemon --spin-time 5 --timeout 8 >"$tmp_out" 2>/dev/null &
else
  ros2 topic echo /g1/task_plan --once --no-daemon --spin-time 5 --timeout 8 >"$tmp_out" 2>/dev/null &
fi
echo_pid=$!

sleep 1.5

echo "Publishing: ${CMD_TEXT}" >&2
# Note: args are joined by the node itself.
for _i in 1 2 3; do
  ros2 run g1_nl_commands nl_command_tester ${CMD_TEXT}
  sleep 0.3
done

wait "$echo_pid" >/dev/null 2>&1 || true
if [[ -s "$tmp_out" ]]; then
  echo "--- /g1/task_plan ---"
  cat "$tmp_out"
else
  echo "ERROR: Did not receive /g1/task_plan output (timeout or no publish)." >&2
  exit 2
fi
