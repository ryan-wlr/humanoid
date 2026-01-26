#!/usr/bin/env bash
set -euo pipefail

# Persists ROS 2 environment defaults in ~/.bashrc for WSL.
# Safe to run multiple times.

DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
RMW="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"
DISCOVERY_PORT="${ROS_DISCOVERY_SERVER_PORT:-11812}"

BASHRC="$HOME/.bashrc"
MARKER_BEGIN="# >>> ros2_ws defaults >>>"
MARKER_END="# <<< ros2_ws defaults <<<"

PROFILE="$HOME/.profile"
PROFILE_MARKER_BEGIN="# >>> ros2_ws defaults (login) >>>"
PROFILE_MARKER_END="# <<< ros2_ws defaults (login) <<<"

tmp="$(mktemp)"

# Remove existing block if present
if [[ -f "$BASHRC" ]]; then
  awk -v b="$MARKER_BEGIN" -v e="$MARKER_END" '
    $0==b {skip=1; next}
    $0==e {skip=0; next}
    !skip {print}
  ' "$BASHRC" > "$tmp"
else
  : > "$tmp"
fi

cat >> "$tmp" <<EOF
$MARKER_BEGIN
# Isaac Sim + ROS 2 in WSL: keep these consistent
export ROS_DOMAIN_ID=$DOMAIN_ID
export RMW_IMPLEMENTATION=$RMW
export ROS_LOCALHOST_ONLY=0
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4

# Discovery Server mode (optional):
# Do NOT auto-set ROS_DISCOVERY_SERVER here.
# If you set it but the server is not running/reachable, your ROS graph may look empty.
#
# To use Fast DDS Discovery Server from WSL, start the server in WSL and then set:
#   export ROS_DISCOVERY_SERVER=127.0.0.1:$DISCOVERY_PORT
#
# For Windows Isaac Sim, set ROS_DISCOVERY_SERVER to the WSL NAT IP (from `hostname -I`) with the same port.

# Auto-source ROS 2 (optional). Comment out if you prefer manual sourcing.
if [ -f /opt/ros/jazzy/setup.bash ]; then
  source /opt/ros/jazzy/setup.bash
fi
$MARKER_END
EOF

mv "$tmp" "$BASHRC"

# Also update ~/.profile so these vars apply to login shells invoked via `bash -lc`
# (common when starting commands from Windows via wsl.exe). Many ~/.bashrc files
# early-return for non-interactive shells, which would otherwise skip our exports.
tmp2="$(mktemp)"

if [[ -f "$PROFILE" ]]; then
  awk -v b="$PROFILE_MARKER_BEGIN" -v e="$PROFILE_MARKER_END" '
    $0==b {skip=1; next}
    $0==e {skip=0; next}
    !skip {print}
  ' "$PROFILE" > "$tmp2"
else
  : > "$tmp2"
fi

cat >> "$tmp2" <<EOF
$PROFILE_MARKER_BEGIN
# Isaac Sim + ROS 2 in WSL (login shells)
export ROS_DOMAIN_ID=$DOMAIN_ID
export RMW_IMPLEMENTATION=$RMW
export ROS_LOCALHOST_ONLY=0
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4

# Discovery Server mode (optional): see ~/.bashrc block above.

if [ -f /opt/ros/jazzy/setup.bash ]; then
  # shellcheck disable=SC1091
  source /opt/ros/jazzy/setup.bash
fi
$PROFILE_MARKER_END
EOF

mv "$tmp2" "$PROFILE"

echo "Updated $BASHRC with ROS_DOMAIN_ID=$DOMAIN_ID, RMW_IMPLEMENTATION=$RMW"
echo "Also sets ROS_LOCALHOST_ONLY=0 and FASTDDS_BUILTIN_TRANSPORTS=UDPv4."
echo "Note: ROS_DISCOVERY_SERVER is now opt-in (not auto-set), because setting it when no server is running can make the ROS graph appear empty."
echo "Also updated $PROFILE so these apply in login shells (e.g., wsl.exe bash -lc)."
echo "Open a new WSL terminal to pick it up, or run: source ~/.bashrc"