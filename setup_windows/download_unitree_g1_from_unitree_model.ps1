param(
  [string]$RepoUrl = "https://github.com/unitreerobotics/unitree_model.git",
  [string]$Ref = "main",
  # Subdir inside the repo that contains the USD + its configuration folder
  [string]$SparsePath = "G1/29dof/usd/g1_29dof_rev_1_0",
  [switch]$Force
)

$ErrorActionPreference = "Stop"

function Get-RepoRoot() {
  return (Resolve-Path (Join-Path $PSScriptRoot ".." )).Path
}

function Ensure-Git() {
  $git = Get-Command git -ErrorAction SilentlyContinue
  if (-not $git) {
    throw "git not found on PATH. Install Git for Windows and try again."
  }
}

$repoRoot = Get-RepoRoot
$assetsRoot = Join-Path $repoRoot "assets\unitree_g1"
$vendorRoot = Join-Path $assetsRoot "vendor\unitree_model"
$usdRelPath = Join-Path $SparsePath "g1_29dof_rev_1_0.usd"
$usdAbsPath = Join-Path $vendorRoot $usdRelPath
$markerPath = Join-Path $assetsRoot "unitree_g1_usd_path.txt"

Ensure-Git

New-Item -ItemType Directory -Force -Path $assetsRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $vendorRoot) | Out-Null

if ((Test-Path $vendorRoot) -and $Force) {
  Write-Host "Removing existing vendor folder: $vendorRoot" -ForegroundColor DarkYellow
  Remove-Item -Recurse -Force $vendorRoot
}

if (-not (Test-Path $vendorRoot)) {
  Write-Host "Cloning (sparse) $RepoUrl ..." -ForegroundColor Cyan
  git clone --depth 1 --filter=blob:none --sparse --branch $Ref $RepoUrl $vendorRoot
  if ($LASTEXITCODE -ne 0) { throw "git clone failed (exit $LASTEXITCODE)" }

  Write-Host "Configuring sparse checkout: $SparsePath" -ForegroundColor Cyan
  git -C $vendorRoot sparse-checkout set $SparsePath
  if ($LASTEXITCODE -ne 0) { throw "git sparse-checkout failed (exit $LASTEXITCODE)" }
} else {
  Write-Host "Updating existing checkout..." -ForegroundColor Cyan
  git -C $vendorRoot fetch --depth 1 origin $Ref
  git -C $vendorRoot checkout $Ref
  git -C $vendorRoot sparse-checkout set $SparsePath
  git -C $vendorRoot pull --ff-only
}

if (-not (Test-Path $usdAbsPath)) {
  throw "Expected USD not found at: $usdAbsPath"
}

Set-Content -Path $markerPath -Value $usdAbsPath -Encoding utf8

Write-Host "\nDownloaded Unitree G1 USD:" -ForegroundColor Green
Write-Host "  $usdAbsPath" -ForegroundColor Green
Write-Host "\nSaved path marker:" -ForegroundColor DarkCyan
Write-Host "  $markerPath" -ForegroundColor DarkCyan
Write-Host "\nTo launch Isaac Sim with this model:" -ForegroundColor Cyan
Write-Host "  run_unitree_g1_windows.cmd" -ForegroundColor Cyan
Write-Host "\nOr set env var explicitly in a PowerShell session:" -ForegroundColor Cyan
Write-Host "  `$env:UNITREE_G1_USD = '$usdAbsPath'" -ForegroundColor Cyan
