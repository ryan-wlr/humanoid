param(
  [string]$IsaacRoot = "C:\\isaacsim",
  [string]$IsaacAppKit = "isaacsim.exp.full.kit",
  [string]$IsaacRosDistro = "jazzy",
  [string]$DomainId = "0",
  [switch]$LocalhostOnly,
  [bool]$EnableRos2Bridge = $true,
  [switch]$FixBlackViewport,
  [switch]$ResetKitUserConfig,
  [switch]$OpenRoboticsExamples,
  [switch]$ForceDownload,
  [switch]$Detach
)

$ErrorActionPreference = "Stop"

# Defaults: detach unless the user asked otherwise.
if (-not $PSBoundParameters.ContainsKey('Detach')) { $Detach = $true }

$repoRoot = Split-Path -Parent $PSScriptRoot

# 1) Ensure OpenUSD Kitchen Set exists locally (writes marker file used by the exec script).
$dl = Join-Path $PSScriptRoot "download_openusd_kitchen_set.ps1"
if (-not (Test-Path $dl)) {
  throw "Missing kitchen download script: $dl"
}

$dlArgs = @{
  OutDir = (Join-Path $repoRoot "assets\kitchen_set")
}
if ($ForceDownload) { $dlArgs.Force = $true }
& $dl @dlArgs

# 2) Launch Isaac Sim with the dedicated kitchen+G1 exec script.
$launcher = Join-Path $PSScriptRoot "launch_isaac_sim_with_ros2.ps1"
if (-not (Test-Path $launcher)) {
  throw "Missing launcher: $launcher"
}

$execScript = Join-Path $PSScriptRoot "auto_load_unitree_g1_into_kitchen.py"
if (-not (Test-Path $execScript)) {
  throw "Missing exec script: $execScript"
}

Write-Host "\nLaunching Isaac Sim (kitchen + Unitree G1)..." -ForegroundColor Cyan

$launcherParams = @{
  IsaacRoot             = $IsaacRoot
  DomainId              = $DomainId
  DiscoveryServer       = ""   # Windows-only default
  WslDistro             = "Ubuntu-24.04"
  LocalhostOnly         = $LocalhostOnly
  EnableRos2Bridge      = $EnableRos2Bridge
  RosDistro             = $IsaacRosDistro
  ForceRosDistroSetting = $true
  FixBlackViewport      = $FixBlackViewport
  ResetKitUserConfig    = $ResetKitUserConfig
  OpenRoboticsExamples  = $OpenRoboticsExamples
  ExecScript            = $execScript
  Mode                  = "kit"
  AppKit                = $IsaacAppKit
  Detach                = $Detach
}

& $launcher @launcherParams
