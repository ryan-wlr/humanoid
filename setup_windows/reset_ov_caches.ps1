param(
  [string]$OvRoot = "",
  [switch]$StopKit,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OvRoot)) {
  $OvRoot = Join-Path $env:LOCALAPPDATA "ov"
}

$cacheRoot = Join-Path $OvRoot "cache"
if (-not (Test-Path $cacheRoot)) {
  throw "Cache root not found: $cacheRoot"
}

if ($StopKit) {
  Get-Process kit -ErrorAction SilentlyContinue | Stop-Process -Force
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$targets = @(
  "Kit",
  "shaders",
  "DerivedDataCache",
  "texturecache"
)

Write-Host "OV cache reset:" -ForegroundColor Cyan
Write-Host "  OvRoot:     $OvRoot" -ForegroundColor DarkCyan
Write-Host "  CacheRoot:  $cacheRoot" -ForegroundColor DarkCyan
Write-Host "  Backup tag: $stamp" -ForegroundColor DarkCyan

foreach ($name in $targets) {
  $src = Join-Path $cacheRoot $name
  if (-not (Test-Path $src)) {
    Write-Host "  SKIP (missing): $src" -ForegroundColor DarkYellow
    continue
  }

  $dst = "$src.bak_$stamp"
  Write-Host "  MOVE: $src -> $dst" -ForegroundColor Green
  if (-not $DryRun) {
    Move-Item -Path $src -Destination $dst -Force
  }
}

Write-Host "Done. Relaunch Isaac Sim; caches will rebuild." -ForegroundColor Cyan
