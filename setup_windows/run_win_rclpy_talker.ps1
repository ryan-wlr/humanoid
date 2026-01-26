param(
  [string]$IsaacRoot = "C:\\isaacsim",
  [string]$RosDistro = "jazzy",
  [string]$DomainId = "0",
  [string]$DiscoveryServer = "192.168.1.200:11812",
  [switch]$LocalhostOnly,
  [string]$AutomaticDiscoveryRange = "",
  [string]$StaticPeers = "",
  [switch]$UseFastddsXmlDiscoveryServer,
  [string]$FastddsServerIp = "",
  [int]$FastddsServerPort = 11812,
  # Detach by default so this script can be used from automation without being interrupted.
  # Pass `-Detach false` to run in the foreground.
  [bool]$Detach = $true
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

$talker = Join-Path $PSScriptRoot "win_rclpy_talker.py"
if (-not (Test-Path $talker)) {
  throw "Not found: $talker"
}

# Configure ROS 2 env for this process.
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

if (-not [string]::IsNullOrWhiteSpace($AutomaticDiscoveryRange)) {
  $env:ROS_AUTOMATIC_DISCOVERY_RANGE = $AutomaticDiscoveryRange
}
if (-not [string]::IsNullOrWhiteSpace($StaticPeers)) {
  $env:ROS_STATIC_PEERS = $StaticPeers
}

if ($UseFastddsXmlDiscoveryServer) {
  if ([string]::IsNullOrWhiteSpace($FastddsServerIp)) {
    # Best-effort: parse from DiscoveryServer if provided.
    if ($DiscoveryServer -match '^(?<ip>[^:]+):(?<port>\d+)$') {
      $FastddsServerIp = $Matches['ip']
      $FastddsServerPort = [int]$Matches['port']
    } else {
      throw "-UseFastddsXmlDiscoveryServer requires -FastddsServerIp (or a parseable -DiscoveryServer like <ip>:<port>)."
    }
  }

  # Remove the ROS_* discovery knobs to avoid conflicts.
  Remove-Item Env:ROS_DISCOVERY_SERVER -ErrorAction SilentlyContinue
  Remove-Item Env:ROS_AUTOMATIC_DISCOVERY_RANGE -ErrorAction SilentlyContinue
  Remove-Item Env:ROS_STATIC_PEERS -ErrorAction SilentlyContinue

  $xmlPath = Join-Path $PSScriptRoot "fastdds_discovery_client.generated.xml"

  # GUID prefix printed by fast-discovery-server for Server ID 0 (stable across restarts).
  $serverGuidPrefix = "44.53.00.5f.45.50.52.4f.53.49.4d.41"

  $xml = @"
<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<profiles xmlns=\"http://www.eprosima.com/XMLSchemas/fastRTPS_Profiles\">
  <participant profile_name=\"ros2_default\" is_default_profile=\"true\">
    <rtps>
      <builtin>
        <discovery_config>
          <discoveryProtocol>CLIENT</discoveryProtocol>
          <discoveryServersList>
            <RemoteServer prefix=\"$serverGuidPrefix\">
              <metatrafficUnicastLocatorList>
                <locator>
                  <udpv4>
                    <address>$FastddsServerIp</address>
                    <port>$FastddsServerPort</port>
                  </udpv4>
                </locator>
              </metatrafficUnicastLocatorList>
            </RemoteServer>
          </discoveryServersList>
        </discovery_config>
      </builtin>
    </rtps>
  </participant>
</profiles>
"@

  Set-Content -Path $xmlPath -Value $xml -Encoding UTF8

  $env:FASTRTPS_DEFAULT_PROFILES_FILE = $xmlPath
  $env:RMW_FASTRTPS_USE_QOS_FROM_XML = "1"
}

# Ensure Isaac-shipped ROS 2 DLLs and Python packages are used.
if ($env:PATH -notlike "*$rosBridgeLib*") {
  $env:PATH = "$rosBridgeLib;$env:PATH"
}
if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) {
  $env:PYTHONPATH = $rosBridgePy
} else {
  # Prepend to prefer Isaac-shipped rclpy, but keep any existing paths.
  $env:PYTHONPATH = "$rosBridgePy;$env:PYTHONPATH"
}

Write-Host "Running Windows talker..." -ForegroundColor Cyan
Write-Host "  ROS_DISTRO=$env:ROS_DISTRO" -ForegroundColor DarkCyan
Write-Host "  ROS_DOMAIN_ID=$env:ROS_DOMAIN_ID" -ForegroundColor DarkCyan
Write-Host "  ROS_DISCOVERY_SERVER=$env:ROS_DISCOVERY_SERVER" -ForegroundColor DarkCyan
if ($env:ROS_AUTOMATIC_DISCOVERY_RANGE) {
  Write-Host "  ROS_AUTOMATIC_DISCOVERY_RANGE=$env:ROS_AUTOMATIC_DISCOVERY_RANGE" -ForegroundColor DarkCyan
}
if ($env:ROS_STATIC_PEERS) {
  Write-Host "  ROS_STATIC_PEERS=$env:ROS_STATIC_PEERS" -ForegroundColor DarkCyan
}
if ($env:FASTRTPS_DEFAULT_PROFILES_FILE) {
  Write-Host "  FASTRTPS_DEFAULT_PROFILES_FILE=$env:FASTRTPS_DEFAULT_PROFILES_FILE" -ForegroundColor DarkCyan
}
if ($env:RMW_FASTRTPS_USE_QOS_FROM_XML) {
  Write-Host "  RMW_FASTRTPS_USE_QOS_FROM_XML=$env:RMW_FASTRTPS_USE_QOS_FROM_XML" -ForegroundColor DarkCyan
}

if ($Detach) {
  $outFile = Join-Path $PSScriptRoot "win_rclpy_talker.out.txt"
  $errFile = Join-Path $PSScriptRoot "win_rclpy_talker.err.txt"
  $pidFile = Join-Path $PSScriptRoot "win_rclpy_talker.pid.txt"
  $p = Start-Process -FilePath $pythonBat -ArgumentList @($talker) -WorkingDirectory $PSScriptRoot -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
  Set-Content -Path $pidFile -Value $p.Id -Encoding ASCII
  Write-Host "Detached talker PID: $($p.Id)" -ForegroundColor Green
  Write-Host "  stdout: $outFile" -ForegroundColor DarkCyan
  Write-Host "  stderr: $errFile" -ForegroundColor DarkCyan
  Write-Host "  pid:    $pidFile" -ForegroundColor DarkCyan
  return
}

& $pythonBat $talker
