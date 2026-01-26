#!/usr/bin/env bash
set -euo pipefail

# Forces Fast DDS (rmw_fastrtps_cpp) to use UDPv4 builtin transport.
# This avoids Fast DDS shared-memory transport issues across Windows<->WSL.

# Keep consistent with Isaac Sim (Windows) side by also setting this as a Windows User env var:
#   FASTDDS_BUILTIN_TRANSPORTS=UDPv4

export FASTDDS_BUILTIN_TRANSPORTS="${FASTDDS_BUILTIN_TRANSPORTS:-UDPv4}"

echo "FASTDDS_BUILTIN_TRANSPORTS=$FASTDDS_BUILTIN_TRANSPORTS"