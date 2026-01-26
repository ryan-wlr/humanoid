param(
  [string]$WslDistro = "Ubuntu-24.04",
  [string]$IsaacRoot = "C:\\isaacsim",
  # A lighter default than Isaac Sim Full to reduce UI hangs. Override with e.g. "isaacsim.exp.full.kit".
  [string]$IsaacAppKit = "isaacsim.exp.base.kit",

  # ROS 2 distro used by Isaac Sim's ROS2 bridge on Windows.
  # Defaulting to Jazzy aligns with WSL Ubuntu 24.04 (Jazzy) and avoids ROS graph incompatibilities across distros.
  [string]$IsaacRosDistro = "jazzy",

  [string]$DomainId = "0",

  # Discovery server runs in WSL. Windows (Isaac Sim) must point at WSL's current IP.
  # If unset, this script auto-detects the WSL IP.
  [string]$DiscoveryServerIp = "",
  [int]$DiscoveryServerPort = 11812,

  [switch]$StartDiscoveryServer,
  [switch]$StartDiffDriveStack,
  [switch]$NoRviz,

  # Git Bash expands `$false` to an empty string, which makes PowerShell boolean args painful.
  # These switches let you disable components without passing `$false`.
  [switch]$SkipDiscoveryServer,
  [switch]$SkipDiffDriveStack,
  [switch]$SkipIsaacSim,

  # Workaround for black viewport on some systems.
  [switch]$FixBlackViewport,

  # Reset Isaac Sim (Kit) user config (often fixes black viewport / broken layouts).
  [switch]$ResetKitUserConfig,

  # Auto-open the Robotics Examples browser (contains ROS2 sample scenes like Nova Carter).
  [switch]$OpenRoboticsExamples,

  # Prompt for elevation (UAC) and install Windows Firewall rules for kit.exe UDP.
  # This is often required for Windows<->WSL discovery server setups.
  [switch]$EnsureFirewallRules,

  [switch]$LaunchIsaacSim
)

$ErrorActionPreference = "Stop"

# Defaults: start everything unless the user explicitly turns something off.
if (-not $PSBoundParameters.ContainsKey('StartDiscoveryServer')) { $StartDiscoveryServer = $true }
if (-not $PSBoundParameters.ContainsKey('StartDiffDriveStack')) { $StartDiffDriveStack = $true }
if (-not $PSBoundParameters.ContainsKey('LaunchIsaacSim')) { $LaunchIsaacSim = $true }

if ($SkipDiscoveryServer) { $StartDiscoveryServer = $false }
if ($SkipDiffDriveStack) { $StartDiffDriveStack = $false }
if ($SkipIsaacSim) { $LaunchIsaacSim = $false }

function Get-WslIp([string]$distro) {
  # Avoid nested bash pipelines/quoting here (they can hang or get mangled depending on the caller shell).
  # Instead, query interface addresses directly and parse in PowerShell.
  $lines = & wsl.exe -d $distro -- ip -4 -brief addr show 2>$null
  foreach ($line in $lines) {
    $s = ($line -as [string]).Trim()
    if (-not $s) { continue }

    # Example: "eth0             UP             172.30.81.27/20"
    if ($s -match "\b(?<ip>(?:\d{1,3}\.){3}\d{1,3})\/") {
      return $Matches.ip
    }
  }

  throw "Failed to resolve WSL IP from distro '$distro'. If WSL just restarted, wait ~10s and retry, or pass -DiscoveryServerIp <WSL_IP> explicitly."
}

if ([string]::IsNullOrWhiteSpace($DiscoveryServerIp)) {
  $DiscoveryServerIp = Get-WslIp $WslDistro
}

$discoveryAddr = "$DiscoveryServerIp`:$DiscoveryServerPort"

function Invoke-WslBash([string]$command) {
  $out = & wsl.exe -d $WslDistro -- bash -lc $command 2>&1
  $code = $LASTEXITCODE
  if ($code -ne 0) {
    $text = ($out | Out-String).TrimEnd()
    throw "WSL command failed (exit $code): $command`n--- WSL output ---`n$text"
  }
  return $out
}

function Ensure-KitFirewallRules([string]$isaacRoot) {
  $fwScript = Join-Path $PSScriptRoot "add_firewall_rules_for_isaacsim_ros2.ps1"
  if (-not (Test-Path $fwScript)) {
    throw "Missing firewall rule script: $fwScript"
  }

  Write-Host "\nInstalling Windows Firewall rules for kit.exe (requires UAC)..." -ForegroundColor Cyan
  $args = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$fwScript`"",
    "-IsaacRoot", "`"$isaacRoot`""
  )

  $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList ($args -join ' ') -Wait -PassThru
  if ($p.ExitCode -ne 0) {
    throw "Firewall rule installer failed (exit $($p.ExitCode))."
  }
}

function Ensure-DdsPortFirewallRules() {
  $fwScript = Join-Path $PSScriptRoot "add_firewall_rules_for_dds_ports.ps1"
  if (-not (Test-Path $fwScript)) {
    throw "Missing firewall rule script: $fwScript"
  }

  Write-Host "\nInstalling Windows Firewall rules for DDS/RTPS UDP ports (requires UAC)..." -ForegroundColor Cyan
  $args = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$fwScript`""
  )

  $p = Start-Process -FilePath "powershell.exe" -Verb RunAs -ArgumentList ($args -join ' ') -Wait -PassThru
  if ($p.ExitCode -ne 0) {
    throw "DDS port firewall rule installer failed (exit $($p.ExitCode))."
  }
}

Write-Host "Starting services..." -ForegroundColor Cyan
Write-Host "  WSL distro: $WslDistro"
Write-Host "  ROS_DOMAIN_ID: $DomainId"
Write-Host "  ROS_DISCOVERY_SERVER: $discoveryAddr"

if ($EnsureFirewallRules) {
  Ensure-KitFirewallRules -isaacRoot $IsaacRoot
  Ensure-DdsPortFirewallRules
}

# 1) Start Fast DDS Discovery Server in WSL (background)
if ($StartDiscoveryServer) {
  Write-Host "\n[1/3] Starting Fast DDS discovery server (WSL)..." -ForegroundColor Cyan

  # Keep as a single line to avoid quoting/newline edge cases across wsl.exe.
  $cmdParts = @(
    'set -e;',
    'if [ ! -x /opt/ros/jazzy/bin/fast-discovery-server ]; then echo ERROR: /opt/ros/jazzy/bin/fast-discovery-server not found. Install ROS 2 Jazzy. 1>&2; exit 10; fi;',
    # Required for shared libraries when invoked non-interactively.
    'export LD_LIBRARY_PATH=/opt/ros/jazzy/lib:/opt/ros/jazzy/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH;',
    'nohup /opt/ros/jazzy/bin/fast-discovery-server -i 0 -p {0} >$HOME/.ros2ws_fastdds_{0}.log & echo Started discovery server PID $!; echo Log: $HOME/.ros2ws_fastdds_{0}.log;'
  )
  $cmd = (($cmdParts -join ' ') -f $DiscoveryServerPort)

  Invoke-WslBash $cmd
}

# 2) Start diff_drive stack in WSL (background)
if ($StartDiffDriveStack) {
  Write-Host "\n[2/3] Starting diff_drive Gazebo stack (WSL, background)..." -ForegroundColor Cyan

  $args = @("--force-x11", "--reset-gui")
  if ($NoRviz) { $args += "--no-rviz" }
  $argsJoined = ($args -join " ")

  $cmdParts = @(
    'set -e;',
    'SCRIPT=/mnt/c/Users/ryan_/Documents/github/ros2_ws/run_diff_drive_stack.sh;',
    'if [ ! -f $SCRIPT ]; then echo ERROR: Missing $SCRIPT 1>&2; exit 20; fi;',
    'export ROS_DOMAIN_ID={1}; export ROS_LOCALHOST_ONLY=0; export RMW_IMPLEMENTATION=rmw_fastrtps_cpp; export FASTDDS_BUILTIN_TRANSPORTS=UDPv4; export ROS_DISCOVERY_SERVER={2};',
    'nohup $SCRIPT {0} >$HOME/.ros2ws_diff_drive_stack.log 2>&1 & echo Started diff_drive stack PID $!; echo Log: $HOME/.ros2ws_diff_drive_stack.log'
  )
  $cmd = (($cmdParts -join ' ') -f $argsJoined, $DomainId, $discoveryAddr)

  Invoke-WslBash $cmd
}

# 3) Launch Isaac Sim on Windows (detached)
if ($LaunchIsaacSim) {
  Write-Host "\n[3/3] Launching Isaac Sim (Windows, detached)..." -ForegroundColor Cyan

  $launcher = Join-Path $PSScriptRoot "launch_isaac_sim_with_ros2.ps1"
  if (-not (Test-Path $launcher)) {
    throw "Missing launcher: $launcher"
  }

  # Invoke the launcher script directly so PowerShell types (bools) are preserved.
  try {
    & $launcher -IsaacRoot $IsaacRoot -DomainId $DomainId -DiscoveryServer $discoveryAddr -RosDistro $IsaacRosDistro -ForceRosDistroSetting:$true -Mode "kit" -AppKit $IsaacAppKit -Detach -FixBlackViewport:$FixBlackViewport -ResetKitUserConfig:$ResetKitUserConfig -OpenRoboticsExamples:$OpenRoboticsExamples
    if (-not $?) {
      throw "Launcher script returned a failure status."
    }
  } catch {
    throw "Isaac Sim launcher failed: $($_.Exception.Message)"
  }
}

# Write a tiny marker file for easy verification (useful when terminals freeze or output is truncated).
try {
  $marker = Join-Path $PSScriptRoot "start_everything.last_run.txt"
  $lines = @(
    "timestamp_utc=$([DateTime]::UtcNow.ToString('o'))",
    "wsl_distro=$WslDistro",
    "ros_domain_id=$DomainId",
    "ros_discovery_server=$discoveryAddr",
    "isaac_root=$IsaacRoot",
    "isaac_app_kit=$IsaacAppKit",
    "isaac_ros_distro=$IsaacRosDistro",
    "started_discovery_server=$StartDiscoveryServer",
    "started_diff_drive_stack=$StartDiffDriveStack",
    "launched_isaac_sim=$LaunchIsaacSim"
  )
  Set-Content -Path $marker -Value ($lines -join "`n") -Encoding UTF8
} catch {
  # Non-fatal.
}

Write-Host "\nAll start commands issued." -ForegroundColor Green
Write-Host "Next: open Isaac Sim, load a ROS2 sample scene, then hit Play." -ForegroundColor Green
Write-Host "\nWSL logs:" -ForegroundColor DarkCyan
Write-Host "  ~/.ros2ws_fastdds_${DiscoveryServerPort}.log"
Write-Host "  ~/.ros2ws_diff_drive_stack.log"
