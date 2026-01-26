#!/usr/bin/env bash
set -euo pipefail

PORT="${1:-11812}"
ROS_BIN="/opt/ros/jazzy/bin/fast-discovery-server"
SERVICE_DIR="$HOME/.config/systemd/user"
SERVICE_PATH="$SERVICE_DIR/fastdds-discovery.service"

if [[ ! -x "$ROS_BIN" ]]; then
  echo "ERROR: $ROS_BIN not found/executable. Install ROS 2 Jazzy first." >&2
  exit 10
fi

mkdir -p "$SERVICE_DIR"

cat >"$SERVICE_PATH" <<EOF
[Unit]
Description=Fast DDS Discovery Server (ROS 2 cross-machine discovery)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
# When started via systemd, ROS 2 environment isn't sourced, so shared libs in
# /opt/ros/jazzy aren't discoverable unless we provide LD_LIBRARY_PATH.
Environment="LD_LIBRARY_PATH=/opt/ros/jazzy/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu"
ExecStart=$ROS_BIN -i 0 -p $PORT
Restart=on-failure
RestartSec=1

# Keep output visible via: journalctl --user -u fastdds-discovery -f
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now fastdds-discovery.service

echo
systemctl --user --no-pager --full status fastdds-discovery.service || true

echo
echo "Listening sockets:" 
ss -lunp | grep ":${PORT}" || true

echo
echo "Tip: follow logs with: journalctl --user -u fastdds-discovery -f"
