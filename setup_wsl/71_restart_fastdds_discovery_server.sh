#!/usr/bin/env bash
set -euo pipefail

# Restarts the ROS 2 Jazzy Fast DDS Discovery Server in WSL.
# Uses the ROS-shipped binary: /opt/ros/jazzy/bin/fast-discovery-server

PORT="${1:-11812}"
LOGFILE="${2:-$HOME/.ros2ws_fastdds_${PORT}.log}"

if [[ ! -x /opt/ros/jazzy/bin/fast-discovery-server ]]; then
  echo "ERROR: /opt/ros/jazzy/bin/fast-discovery-server not found. Install ROS 2 Jazzy." >&2
  exit 10
fi

# Kill any process currently bound to UDP PORT.
if command -v ss >/dev/null 2>&1; then
  mapfile -t pids < <(
    ss -lunpH 2>/dev/null |
      awk -v port=":${PORT}" '$5 ~ port { match($0, /pid=([0-9]+)/, m); if (m[1] != "") print m[1]; }' |
      sort -u
  )

  if (( ${#pids[@]} > 0 )); then
    echo "Killing existing UDP :${PORT} owners: ${pids[*]}" >&2
    for pid in "${pids[@]}"; do
      kill "$pid" 2>/dev/null || true
    done
    sleep 0.5
  fi
fi

# Also kill any stray discovery servers (best-effort).
# This avoids the confusing situation where an older server is running but logging elsewhere.
pkill -x fast-discovery-server 2>/dev/null || true
sleep 0.2

echo "Starting Fast DDS Discovery Server on UDP ${PORT}" >&2
: > "$LOGFILE"
nohup /opt/ros/jazzy/bin/fast-discovery-server -i 0 -p "${PORT}" >"$LOGFILE" 2>&1 &
new_pid=$!

sleep 0.5

echo "Started PID ${new_pid}" >&2
if command -v ss >/dev/null 2>&1; then
  ss -lunp | grep ":${PORT}\b" || true
fi

echo "--- log tail (${LOGFILE}) ---" >&2
tail -n 80 "$LOGFILE" || true
