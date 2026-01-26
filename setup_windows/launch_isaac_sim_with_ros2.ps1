param(
  [string]$IsaacRoot = "C:\\isaacsim",
  [string]$DomainId = "0",
  # Set to:
  #   - "<ip>:<port>" (explicit)
  #   - "auto" or "auto:<port>" to resolve WSL's IP automatically
  #   - "wsl" or "wsl:<port>" (alias of auto)
  #   - "" (empty) to disable discovery server and use normal multicast discovery
  [string]$DiscoveryServer = "auto:11812",
  [string]$WslDistro = "Ubuntu-24.04",
  # When true, restrict ROS 2 traffic to localhost only. Useful when running everything on Windows.
  [switch]$LocalhostOnly,
  [bool]$EnableRos2Bridge = $true,
  [string]$RosDistro = "humble",
  [bool]$ForceRosDistroSetting = $true,
  # Some systems show a black viewport when the renderer present path is disabled.
  # This switch forces present back on.
  [switch]$FixBlackViewport,
  # Reset per-user Kit settings (often fixes black viewport / broken layouts).
  # Backs up user.config.json in %LOCALAPPDATA%\ov\data\Kit\<AppName>\<Version>.
  [switch]$ResetKitUserConfig,
  # Show the Robotics Examples browser on startup (contains ROS2 sample scenes like Nova Carter).
  [switch]$OpenRoboticsExamples,
  # Optional Kit startup script to execute (forwarded as: --exec <scriptPath>).
  # This avoids passing values that begin with '-' through PowerShell's parameter binder.
  [string]$ExecScript = "",
  [string[]]$ExtraArgs = @(),
  [ValidateSet("isaac-sim.bat","isaac-sim.selector.bat","kit")]
  [string]$Mode = "kit",
  # For Mode=kit. Can be a .kit filename under <IsaacRoot>\\apps, or an absolute path to a .kit file.
  [string]$AppKit = "isaacsim.exp.full.kit",
  [switch]$Detach
)

function Get-KitAppName([string]$mode, [string]$appKit) {
  # Best-effort mapping to the user-data folder names under:
  #   %LOCALAPPDATA%\ov\data\Kit\<AppName>\<Version>
  if ($mode -eq "isaac-sim.selector.bat") { return "Isaac-Sim_App_Selector" }
  if ($appKit -match '(?i)base') { return "Isaac-Sim Base" }
  if ($appKit -match '(?i)full') { return "Isaac-Sim Full" }
  # Default to Base since we're typically launching the lighter app.
  return "Isaac-Sim Base"
}

function Backup-KitUserConfig([string]$kitAppName) {
  $kitRoot = Join-Path $env:LOCALAPPDATA ("ov\\data\\Kit\\{0}" -f $kitAppName)
  if (!(Test-Path $kitRoot)) {
    Write-Host "  No Kit user-data dir found at: $kitRoot" -ForegroundColor DarkYellow
    return
  }

  $versionDir = Get-ChildItem -Path $kitRoot -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    Select-Object -First 1

  if (-not $versionDir) {
    Write-Host "  No version subdir found under: $kitRoot" -ForegroundColor DarkYellow
    return
  }

  $userConfig = Join-Path $versionDir.FullName "user.config.json"
  if (!(Test-Path $userConfig)) {
    Write-Host "  No user.config.json to reset under: $($versionDir.FullName)" -ForegroundColor DarkYellow
    return
  }

  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $backup = "$userConfig.bak_$stamp"
  Move-Item -Path $userConfig -Destination $backup -Force
  Write-Host "  Backed up user config: $backup" -ForegroundColor DarkCyan
}

function Resolve-WslIp([string]$distro) {
  $ip = (& wsl.exe -d $distro -- bash -lc "hostname -I 2>/dev/null | tr -s ' ' '\n' | head -n 1") | Select-Object -First 1
  $ip = ($ip -as [string]).Trim()
  if (-not $ip) {
    throw "Failed to resolve WSL IP from distro '$distro'. Try: wsl -l -v, and pass -WslDistro <name>."
  }
  return $ip
}

# Auto-resolve WSL IP for ROS_DISCOVERY_SERVER when requested.
if (-not [string]::IsNullOrWhiteSpace($DiscoveryServer) -and $DiscoveryServer -match '^(auto|wsl)(?::(\d+))?$') {
  $port = if ($Matches[2]) { $Matches[2] } else { "11812" }
  $wslIp = Resolve-WslIp $WslDistro
  $DiscoveryServer = "$wslIp`:$port"
}

# Set process-local env vars so Isaac Sim inherits them even if user vars didn't apply yet.
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

# Isaac Sim's ROS2 bridge ships its own Windows DLLs (including rmw_fastrtps_cpp.dll).
# Ensure they're on PATH so the bridge can load.
$rosBridgeLib = Join-Path $IsaacRoot ("exts\\isaacsim.ros2.bridge\\{0}\\lib" -f $RosDistro)
if (Test-Path $rosBridgeLib) {
  # Prepend so Isaac Sim reliably picks its shipped ROS 2 bridge DLLs first.
  if ($env:PATH -notlike "*$rosBridgeLib*") {
    $env:PATH = "$rosBridgeLib;$env:PATH"
  }
  Write-Host "  PATH += $rosBridgeLib" -ForegroundColor DarkCyan
} else {
  Write-Warning "ROS2 bridge lib dir not found: $rosBridgeLib"
}

Write-Host "Launching Isaac Sim with:" -ForegroundColor Cyan
Write-Host "  ROS_DOMAIN_ID=$env:ROS_DOMAIN_ID"
Write-Host "  ROS_LOCALHOST_ONLY=$env:ROS_LOCALHOST_ONLY"
Write-Host "  ROS_DISTRO=$env:ROS_DISTRO"
Write-Host "  RMW_IMPLEMENTATION=$env:RMW_IMPLEMENTATION"
Write-Host "  FASTDDS_BUILTIN_TRANSPORTS=$env:FASTDDS_BUILTIN_TRANSPORTS"
if ($env:ROS_DISCOVERY_SERVER) {
  Write-Host "  ROS_DISCOVERY_SERVER=$env:ROS_DISCOVERY_SERVER"
} else {
  Write-Host "  ROS_DISCOVERY_SERVER=(disabled)" -ForegroundColor DarkCyan
}

$kitArgs = @()
if ($EnableRos2Bridge) {
  # Isaac Sim has shipped both names historically; enabling both is harmless.
  $kitArgs += @("--enable", "isaacsim.ros2.bridge")
  $kitArgs += @("--enable", "omni.isaac.ros2_bridge")

  # Ensure the ROS2 bridge doesn't try to use an external/system ROS install on Windows.
  # This mirrors settings documented inside:
  #   C:\isaacsim\exts\isaacsim.ros2.bridge\config\extension.toml
  if ($ForceRosDistroSetting -and $RosDistro) {
    $kitArgs += "--/exts/isaacsim.ros2.bridge/ros_distro=`"$RosDistro`""
  }
}

if ($FixBlackViewport) {
  # Override defaults in isaacsim.exp.base.kit:
  #   exts."omni.kit.renderer.core".present.enabled = false
  $kitArgs += "--/exts/omni.kit.renderer.core/present/enabled=true"
}

if ($OpenRoboticsExamples) {
  # Auto-open the Examples Browser window titled "Robotics Examples".
  $kitArgs += "--/exts/isaacsim.examples.browser/visible_after_startup=true"
}

if ($ResetKitUserConfig) {
  $kitAppName = Get-KitAppName -mode $Mode -appKit $AppKit
  Write-Host "Resetting Kit user config for '$kitAppName'..." -ForegroundColor Cyan
  Backup-KitUserConfig -kitAppName $kitAppName
}

if (-not [string]::IsNullOrWhiteSpace($ExecScript)) {
  if (!(Test-Path $ExecScript)) {
    throw "ExecScript not found: $ExecScript"
  }
  $kitArgs += @("--exec", $ExecScript)
}

if ($ExtraArgs.Count -gt 0) {
  $kitArgs += $ExtraArgs
}

if (!(Test-Path $IsaacRoot)) {
  throw "IsaacRoot not found: $IsaacRoot"
}

Set-Location $IsaacRoot

switch ($Mode) {
  "isaac-sim.bat" {
    $bat = Join-Path $IsaacRoot "isaac-sim.bat"
    if (!(Test-Path $bat)) { throw "Not found: $bat" }
    Write-Host "\nRunning: $bat $($kitArgs -join ' ')" -ForegroundColor Green
    if ($Detach) {
      $p = Start-Process -FilePath $bat -ArgumentList $kitArgs -WorkingDirectory $IsaacRoot -PassThru
      Write-Host "Detached Isaac Sim (PID $($p.Id))" -ForegroundColor Cyan
      return
    }
    & $bat @kitArgs
  }
  "isaac-sim.selector.bat" {
    $bat = Join-Path $IsaacRoot "isaac-sim.selector.bat"
    if (!(Test-Path $bat)) { throw "Not found: $bat" }
    Write-Host "\nRunning: $bat $($kitArgs -join ' ')" -ForegroundColor Green
    if ($Detach) {
      $p = Start-Process -FilePath $bat -ArgumentList $kitArgs -WorkingDirectory $IsaacRoot -PassThru
      Write-Host "Detached Isaac Sim (PID $($p.Id))" -ForegroundColor Cyan
      return
    }
    & $bat @kitArgs
  }
  "kit" {
    $kitExe = Join-Path $IsaacRoot "kit\\kit.exe"
    $appKitPath = $null
    if ([System.IO.Path]::IsPathRooted($AppKit)) {
      $appKitPath = $AppKit
    } else {
      $appKitPath = Join-Path $IsaacRoot ("apps\\{0}" -f $AppKit)
    }
    if (!(Test-Path $kitExe)) { throw "Not found: $kitExe" }
    if (!(Test-Path $appKitPath)) { throw "Not found: $appKitPath" }
    Write-Host "\nRunning: $kitExe $appKitPath $($kitArgs -join ' ')" -ForegroundColor Green
    if ($Detach) {
      $args = @($appKitPath) + $kitArgs
      $p = Start-Process -FilePath $kitExe -ArgumentList $args -WorkingDirectory $IsaacRoot -PassThru
      Write-Host "Detached Isaac Sim (PID $($p.Id))" -ForegroundColor Cyan
      return
    }
    & $kitExe $appKitPath @kitArgs
  }
}
