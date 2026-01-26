#!/usr/bin/env bash
set -euo pipefail

# Persists ROS 2 Humble environment defaults in ~/.bashrc for WSL Ubuntu 22.04.
# Safe to run multiple times.

DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
RMW="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"
UDP_ONLY="${FASTDDS_BUILTIN_TRANSPORTS:-UDPv4}"
DISCOVERY_SERVER="${ROS_DISCOVERY_SERVER:-}"

BASHRC="$HOME/.bashrc"
MARKER_BEGIN="# >>> ros2_ws humble defaults >>>"
MARKER_END="# <<< ros2_ws humble defaults <<<"

tmp="$(mktemp)"

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
# Isaac Sim (Windows) + ROS 2 (WSL Ubuntu 22.04): keep these consistent
export ROS_DOMAIN_ID=$DOMAIN_ID
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=$RMW
export FASTDDS_BUILTIN_TRANSPORTS=$UDP_ONLY
EOF

if [[ -n "$DISCOVERY_SERVER" ]]; then
cat >> "$tmp" <<EOF
export ROS_DISCOVERY_SERVER=$DISCOVERY_SERVER
EOF
fi

cat >> "$tmp" <<'EOF'
# Auto-source ROS 2 Humble (optional)
if [ -f /opt/ros/humble/setup.bash ]; then
  source /opt/ros/humble/setup.bash
fi
$MARKER_END
EOF

mv "$tmp" "$BASHRC"

echo "Updated $BASHRC"
echo "- ROS_DOMAIN_ID=$DOMAIN_ID"
echo "- RMW_IMPLEMENTATION=$RMW"
echo "- FASTDDS_BUILTIN_TRANSPORTS=$UDP_ONLY"
if [[ -n "$DISCOVERY_SERVER" ]]; then
  echo "- ROS_DISCOVERY_SERVER=$DISCOVERY_SERVER"
fi

echo "Open a new WSL terminal or run: source ~/.bashrc"