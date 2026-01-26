param(
  [string]$IsaacRoot = "C:\\isaacsim",
  [string]$RosDistro = "jazzy",
  [string]$DomainId = "0",
  [switch]$LocalhostOnly,
  [switch]$NoLocalhostOnly,
  # Set to "" to disable discovery server.
  [string]$DiscoveryServer = "",
  [bool]$Detach = $false
)

$ErrorActionPreference = "Stop"

$pythonBat = Join-Path $IsaacRoot "python.bat"
if (-not (Test-Path $pythonBat)) {
  throw "Not found: $pythonBat"
}

$rosBridgeLib = Join-Path $IsaacRoot ("exts\\isaacsim.ros2.bridge\\{0}\\lib" -f $RosDistro)
$rosBridgePy  = Join-Path $IsaacRoot ("exts\\isaacsim.ros2.bridge\\{0}\\rclpy" -f $RosDistro)

if (-not (Test-Path $rosBridgeLib)) {
  throw "Not found: $rosBridgeLib"
}
if (-not (Test-Path $rosBridgePy)) {
  throw "Not found: $rosBridgePy"
}

$script = Join-Path $PSScriptRoot "win_ros2_graph_dump.py"
if (-not (Test-Path $script)) {
  throw "Not found: $script"
}

# Default to normal subnet discovery unless the caller explicitly chose otherwise.
if (-not $PSBoundParameters.ContainsKey('LocalhostOnly') -and -not $PSBoundParameters.ContainsKey('NoLocalhostOnly')) {
  $LocalhostOnly = $false
}
if ($NoLocalhostOnly) {
  $LocalhostOnly = $false
}

$env:ROS_DOMAIN_ID              = $DomainId
$env:ROS_LOCALHOST_ONLY         = if ($LocalhostOnly) { "1" } else { "0" }
$env:ROS_DISTRO                 = $RosDistro
$env:RMW_IMPLEMENTATION         = "rmw_fastrtps_cpp"
$env:FASTDDS_BUILTIN_TRANSPORTS = "UDPv4"
if (-not [string]::IsNullOrWhiteSpace($DiscoveryServer)) {
  $env:ROS_DISCOVERY_SERVER = $DiscoveryServer
} else {
  Remove-Item Env:ROS_DISCOVERY_SERVER -ErrorAction SilentlyContinue
}

if ($env:PATH -notlike "*$rosBridgeLib*") {
  $env:PATH = "$rosBridgeLib;$env:PATH"
}
if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
  $env:PYTHONPATH = $rosBridgePy
} else {
  $env:PYTHONPATH = "$rosBridgePy;$env:PYTHONPATH"
}

Write-Host "Running Windows ROS2 graph dump..." -ForegroundColor Cyan
Write-Host "  ROS_DISTRO=$env:ROS_DISTRO" -ForegroundColor DarkCyan
Write-Host "  ROS_DOMAIN_ID=$env:ROS_DOMAIN_ID" -ForegroundColor DarkCyan
Write-Host "  ROS_LOCALHOST_ONLY=$env:ROS_LOCALHOST_ONLY" -ForegroundColor DarkCyan
if ($env:ROS_DISCOVERY_SERVER) {
  Write-Host "  ROS_DISCOVERY_SERVER=$env:ROS_DISCOVERY_SERVER" -ForegroundColor DarkCyan
} else {
  Write-Host "  ROS_DISCOVERY_SERVER=(disabled)" -ForegroundColor DarkCyan
}

if ($Detach) {
  $outFile = Join-Path $PSScriptRoot "win_ros2_graph_dump.out.txt"
  $errFile = Join-Path $PSScriptRoot "win_ros2_graph_dump.err.txt"
  $p = Start-Process -FilePath $pythonBat -ArgumentList @($script) -WorkingDirectory $PSScriptRoot -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
  Write-Host "Detached graph dump PID: $($p.Id)" -ForegroundColor Green
  Write-Host "  stdout: $outFile" -ForegroundColor DarkCyan
  Write-Host "  stderr: $errFile" -ForegroundColor DarkCyan
  return
}

& $pythonBat $script
