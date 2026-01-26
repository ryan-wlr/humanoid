param(
  [string]$IsaacRoot = "C:\\isaacsim",
  [string]$IsaacAppKit = "isaacsim.exp.full.kit",
  [string]$IsaacRosDistro = "jazzy",
  [string]$DomainId = "0",
  [switch]$FixBlackViewport,
  [switch]$ResetKitUserConfig,
  [switch]$ForceDownload
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

$dl = Join-Path $PSScriptRoot "download_openusd_kitchen_set.ps1"
if (-not (Test-Path $dl)) { throw "Missing: $dl" }

$dlArgs = @()
if ($ForceDownload) { $dlArgs += "-Force" }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $dl @dlArgs

$marker = Join-Path $repoRoot "assets\kitchen_set\kitchen_set_usd_path.txt"
if (-not (Test-Path $marker)) { throw "Missing marker: $marker" }
$stageUsd = (Get-Content -Path $marker -Raw).Trim()
if ([string]::IsNullOrWhiteSpace($stageUsd) -or -not (Test-Path $stageUsd)) {
  throw "Kitchen stage USD path invalid: '$stageUsd'"
}

$env:UNITREE_STAGE_USD = $stageUsd

$start = Join-Path $PSScriptRoot "start_everything_windows.ps1"
if (-not (Test-Path $start)) { throw "Missing: $start" }

$startArgs = @(
  "-IsaacRoot", $IsaacRoot,
  "-IsaacAppKit", $IsaacAppKit,
  "-IsaacRosDistro", $IsaacRosDistro,
  "-DomainId", $DomainId,
  "-AutoLoadUnitreeG1"
)
if ($FixBlackViewport) { $startArgs += "-FixBlackViewport" }
if ($ResetKitUserConfig) { $startArgs += "-ResetKitUserConfig" }

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $start @startArgs
