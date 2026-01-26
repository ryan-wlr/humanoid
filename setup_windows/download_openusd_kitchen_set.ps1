param(
  [string]$OutDir = "",
  [switch]$Force
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($OutDir)) {
  $OutDir = Join-Path $repoRoot "assets\kitchen_set"
}

$zipUrl = "https://openusd.org/files/Kitchen_set.zip"
$zipPath = Join-Path $OutDir "Kitchen_set.zip"
$extractDir = Join-Path $OutDir "Kitchen_set"
$markerPath = Join-Path $OutDir "kitchen_set_usd_path.txt"

if ($Force) {
  if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
  if (Test-Path $extractDir) { Remove-Item -Recurse -Force $extractDir }
  if (Test-Path $markerPath) { Remove-Item -Force $markerPath }
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

if (-not (Test-Path $extractDir)) {
  Write-Host "Downloading OpenUSD Kitchen Set..." -ForegroundColor Cyan
  Write-Host "  $zipUrl" -ForegroundColor DarkCyan
  Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath

  Write-Host "Extracting..." -ForegroundColor Cyan
  Expand-Archive -Path $zipPath -DestinationPath $OutDir -Force
}

if (-not (Test-Path $extractDir)) {
  throw "Expected extracted folder not found: $extractDir"
}

# Find main Kitchen_set.usd
$usd = Get-ChildItem -Path $extractDir -Recurse -File -Filter "*.usd" |
  Where-Object { $_.Name -match "(?i)^Kitchen[_-]?set\.usd$" } |
  Select-Object -First 1

if (-not $usd) {
  # Fallback: take the first .usd in the extracted folder
  $usd = Get-ChildItem -Path $extractDir -Recurse -File -Filter "*.usd" | Select-Object -First 1
}

if (-not $usd) {
  throw "No .usd file found under: $extractDir"
}

$usdPath = $usd.FullName
Set-Content -Path $markerPath -Value $usdPath -Encoding utf8

Write-Host "Kitchen Set ready:" -ForegroundColor Green
Write-Host "  USD: $usdPath" -ForegroundColor DarkCyan
Write-Host "  Marker: $markerPath" -ForegroundColor DarkCyan
