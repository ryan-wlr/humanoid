param(
  [string]$WslDistro = "Ubuntu-24.04",
  [string]$RosDistro = "jazzy",
  [string]$DomainId = "0",
  [string]$DiscoveryServer = "127.0.0.1:11812"
)

$ErrorActionPreference = "Stop"

$bashScript = @'
set -e

# shellcheck disable=SC1090
source /opt/ros/{ROS_DISTRO}/setup.bash

export ROS_DOMAIN_ID={ROS_DOMAIN_ID}
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
export ROS_DISCOVERY_SERVER={ROS_DISCOVERY_SERVER}

echo --- ROS env ---
echo ROS_DOMAIN_ID=${ROS_DOMAIN_ID}
echo ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER}
echo ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY}
echo RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}
echo FASTDDS_BUILTIN_TRANSPORTS=${FASTDDS_BUILTIN_TRANSPORTS}

echo --- fast discovery server ps ---
ps -ef | grep -E fast-discovery-server\|fastdds | grep -v grep || true

echo --- udp 11812 listener best effort ---
if command -v ss >/dev/null 2>&1; then
  timeout 1s ss -lunp | grep ":11812" || true
fi

echo --- ros2 node list ---
ros2 node list || true

echo --- ros2 topic list first 120 ---
ros2 topic list -t | head -n 120
'@

$bashScript = $bashScript.Replace("{ROS_DISTRO}", $RosDistro)
$bashScript = $bashScript.Replace("{ROS_DOMAIN_ID}", $DomainId)
$bashScript = $bashScript.Replace("{ROS_DISCOVERY_SERVER}", $DiscoveryServer)
$bashScript = $bashScript.Replace("`r`n", "`n")
$bashScript = $bashScript.Replace("`r", "")

# Execute in WSL
& wsl.exe -d $WslDistro -- bash -lc $bashScript
exit $LASTEXITCODE
