param(
  [string]$IsaacRoot = "C:\\isaacsim",
  [string]$IsaacAppKit = "isaacsim.exp.full.kit",
  [string]$IsaacRosDistro = "jazzy",
  [string]$DomainId = "0",
  # Default behavior is full subnet discovery so Isaac Sim topics show up.
  # Use -LocalhostOnly if you want to restrict ROS 2 to loopback.
  [switch]$LocalhostOnly,
  [switch]$FixBlackViewport,
  [switch]$ResetKitUserConfig,
  [switch]$OpenRoboticsExamples,
  # Auto-load the Nova Carter ROS2 sample stage and hit Play on startup.
  [switch]$AutoLoadNovaCarter,
  # Auto-create a stage with a ground plane and spawn Unitree G1, then hit Play.
  [switch]$AutoLoadUnitreeG1,
  # Auto-load the ROS2 warehouse scene, spawn Unitree G1, create a table+apple,
  # then (best-effort) put the apple in the robot's hand.
  [switch]$AutoLoadUnitreeG1WarehouseApplePick,
  # Optional local USD path (or omniverse:// url) used when -AutoLoadUnitreeG1.
  # If omitted, will try to read assets/unitree_g1/unitree_g1_usd_path.txt.
  [string]$UnitreeG1Usd = "",
  [switch]$EnsureFirewallRules,
  [switch]$LaunchIsaacSim,
  [switch]$StartWinTalker,
  [switch]$StartWinListener,
  [switch]$DumpWinGraph,
  # Delay before dumping the graph (helps when Isaac is still starting up).
  # If not specified, a reasonable default is chosen when launching Isaac.
  [int]$GraphDumpDelaySec = -1
)

$ErrorActionPreference = "Stop"

# Defaults: launch Isaac and dump graph unless user explicitly turns off.
if (-not $PSBoundParameters.ContainsKey('LaunchIsaacSim')) { $LaunchIsaacSim = $true }
if (-not $PSBoundParameters.ContainsKey('DumpWinGraph')) { $DumpWinGraph = $true }

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

Write-Host "Starting Windows-only stack..." -ForegroundColor Cyan
Write-Host "  ROS_DOMAIN_ID: $DomainId" -ForegroundColor DarkCyan
$localhostVal = if ($LocalhostOnly) { 1 } else { 0 }
Write-Host "  ROS_LOCALHOST_ONLY: $localhostVal" -ForegroundColor DarkCyan
Write-Host "  ROS_DISCOVERY_SERVER: (disabled)" -ForegroundColor DarkCyan

if ($EnsureFirewallRules) {
  Ensure-KitFirewallRules -isaacRoot $IsaacRoot
}

# 1) Launch Isaac Sim (detached)
if ($LaunchIsaacSim) {
  Write-Host "\n[1/3] Launching Isaac Sim (Windows, detached)..." -ForegroundColor Cyan

  $launcher = Join-Path $PSScriptRoot "launch_isaac_sim_with_ros2.ps1"
  if (-not (Test-Path $launcher)) {
    throw "Missing launcher: $launcher"
  }

  # IMPORTANT: Use hashtable splatting for named parameter binding.
  # Array splatting is positional and will mis-bind parameters.
  $launcherParams = @{
    IsaacRoot            = $IsaacRoot
    DomainId             = $DomainId
    DiscoveryServer      = ""
    RosDistro            = $IsaacRosDistro
    ForceRosDistroSetting = $true
    Mode                 = "kit"
    AppKit               = $IsaacAppKit
    Detach               = $true
  }
  if ($LocalhostOnly) { $launcherParams.LocalhostOnly = $true }
  if ($FixBlackViewport) { $launcherParams.FixBlackViewport = $true }
  if ($ResetKitUserConfig) { $launcherParams.ResetKitUserConfig = $true }
  if ($OpenRoboticsExamples) { $launcherParams.OpenRoboticsExamples = $true }

  if ($AutoLoadNovaCarter) {
    $scriptPath = Join-Path $PSScriptRoot "auto_load_ros2_nova_carter.py"
    if (-not (Test-Path $scriptPath)) {
      throw "Missing auto-load script: $scriptPath"
    }
    $launcherParams.ExecScript = $scriptPath
  }

  function Set-UnitreeG1UsdEnv {
    param([string]$UnitreeG1UsdArg)

    if (-not [string]::IsNullOrWhiteSpace($UnitreeG1UsdArg)) {
      $env:UNITREE_G1_USD = $UnitreeG1UsdArg
      return
    }

    $marker = Join-Path (Join-Path (Split-Path -Parent $PSScriptRoot) "assets") "unitree_g1\unitree_g1_usd_path.txt"
    if (Test-Path $marker) {
      $p = (Get-Content -Path $marker -Raw -Encoding utf8).Trim()
      # Strip UTF-8 BOM if present (can happen if the file was edited elsewhere).
      $p = $p -replace "^\uFEFF", ""
      if (-not [string]::IsNullOrWhiteSpace($p)) {
        $env:UNITREE_G1_USD = $p
      }
    }
  }

  if ($AutoLoadUnitreeG1) {
    if ($launcherParams.ContainsKey('ExecScript') -and -not [string]::IsNullOrWhiteSpace($launcherParams.ExecScript)) {
      throw "Choose only one auto-load option: -AutoLoadNovaCarter, -AutoLoadUnitreeG1, or -AutoLoadUnitreeG1WarehouseApplePick."
    }

    # Provide the robot USD path to the exec script via env var.
    # This is optional: the script also tries Isaac assets-root fallbacks.
    Set-UnitreeG1UsdEnv -UnitreeG1UsdArg $UnitreeG1Usd

    $scriptPath = Join-Path $PSScriptRoot "auto_load_unitree_g1.py"
    if (-not (Test-Path $scriptPath)) {
      throw "Missing auto-load script: $scriptPath"
    }
    $launcherParams.ExecScript = $scriptPath
  }

  if ($AutoLoadUnitreeG1WarehouseApplePick) {
    if ($launcherParams.ContainsKey('ExecScript') -and -not [string]::IsNullOrWhiteSpace($launcherParams.ExecScript)) {
      throw "Choose only one auto-load option: -AutoLoadNovaCarter, -AutoLoadUnitreeG1, or -AutoLoadUnitreeG1WarehouseApplePick."
    }

    Set-UnitreeG1UsdEnv -UnitreeG1UsdArg $UnitreeG1Usd

    $scriptPath = Join-Path $PSScriptRoot "auto_load_unitree_g1_warehouse_apple_pick.py"
    if (-not (Test-Path $scriptPath)) {
      throw "Missing auto-load script: $scriptPath"
    }
    $launcherParams.ExecScript = $scriptPath
  }

  & $launcher @launcherParams
}

# 2) Optional: start a local talker/listener using Isaac's shipped Python + rclpy
if ($StartWinTalker) {
  Write-Host "\n[2/3] Starting Windows talker (Isaac python, detached)..." -ForegroundColor Cyan
  $talker = Join-Path $PSScriptRoot "run_win_rclpy_talker.ps1"
  $talkerParams = @{
    IsaacRoot       = $IsaacRoot
    RosDistro       = $IsaacRosDistro
    DomainId        = $DomainId
    DiscoveryServer = ""
    Detach          = $true
  }
  if ($LocalhostOnly) { $talkerParams.LocalhostOnly = $true }
  & $talker @talkerParams
}

if ($StartWinListener) {
  Write-Host "\n[2/3] Running Windows listener (30s)..." -ForegroundColor Cyan

  $pythonBat = Join-Path $IsaacRoot "python.bat"
  if (-not (Test-Path $pythonBat)) { throw "Not found: $pythonBat" }

  $rosBridgeLib = Join-Path $IsaacRoot ("exts\\isaacsim.ros2.bridge\\{0}\\lib" -f $IsaacRosDistro)
  $rosBridgePy  = Join-Path $IsaacRoot ("exts\\isaacsim.ros2.bridge\\{0}\\rclpy" -f $IsaacRosDistro)
  if ($env:PATH -notlike "*$rosBridgeLib*") { $env:PATH = "$rosBridgeLib;$env:PATH" }
  if ([string]::IsNullOrWhiteSpace($env:PYTHONPATH)) { $env:PYTHONPATH = $rosBridgePy } else { $env:PYTHONPATH = "$rosBridgePy;$env:PYTHONPATH" }

  $env:ROS_DOMAIN_ID = $DomainId
  $env:ROS_LOCALHOST_ONLY = if ($LocalhostOnly) { "1" } else { "0" }
  $env:ROS_DISTRO = $IsaacRosDistro
  $env:RMW_IMPLEMENTATION = "rmw_fastrtps_cpp"
  $env:FASTDDS_BUILTIN_TRANSPORTS = "UDPv4"
  Remove-Item Env:ROS_DISCOVERY_SERVER -ErrorAction SilentlyContinue

  & $pythonBat (Join-Path $PSScriptRoot "win_rclpy_listener.py")
}

# 3) Dump current Windows ROS graph using rclpy (no ros2.exe required)
if ($DumpWinGraph) {
  if ($LaunchIsaacSim) {
    $delaySec = $GraphDumpDelaySec
    if ($delaySec -lt 0) {
      $delaySec = if ($AutoLoadNovaCarter -or $AutoLoadUnitreeG1) { 45 } else { 10 }
    }
    if ($delaySec -gt 0) {
      Write-Host "Waiting ${delaySec}s for Isaac Sim to initialize before graph dump..." -ForegroundColor DarkCyan
      Start-Sleep -Seconds $delaySec
    }
  }

  Write-Host "\n[3/3] Dumping Windows ROS graph..." -ForegroundColor Cyan
  $dump = Join-Path $PSScriptRoot "run_win_ros2_graph_dump.ps1"
  $dumpParams = @{
    IsaacRoot       = $IsaacRoot
    RosDistro       = $IsaacRosDistro
    DomainId        = $DomainId
    DiscoveryServer = ""
  }
  if ($LocalhostOnly) { $dumpParams.LocalhostOnly = $true } else { $dumpParams.NoLocalhostOnly = $true }

  $attempts = if (($AutoLoadNovaCarter -or $AutoLoadUnitreeG1) -and $LaunchIsaacSim) { 3 } else { 1 }
  $retryDelaySec = 15
  for ($i = 1; $i -le $attempts; $i++) {
    if ($attempts -gt 1) {
      Write-Host ("Graph dump attempt {0}/{1}..." -f $i, $attempts) -ForegroundColor DarkCyan
    }

    $lines = @()
    & $dump @dumpParams | Tee-Object -Variable lines
    $dumpText = ($lines -join "`n")

    if ($dumpText -match "(?m)^/clock\s" -or $dumpText -match "(?m)^/tf\s" -or $dumpText -match "(?m)^/cmd_vel\s") {
      break
    }

    if ($i -lt $attempts) {
      Write-Host "No Isaac topics yet (/clock,/tf,/cmd_vel). Retrying in ${retryDelaySec}s..." -ForegroundColor DarkYellow
      Start-Sleep -Seconds $retryDelaySec
    } else {
      Write-Host "Still not seeing Isaac topics. If Isaac is running a ROS scene, try -EnsureFirewallRules (once, UAC) or increase -GraphDumpDelaySec." -ForegroundColor DarkYellow
    }
  }
}

Write-Host "\nDone. If Isaac Sim is playing a ROS scene, its topics should appear in the graph dump." -ForegroundColor Green
