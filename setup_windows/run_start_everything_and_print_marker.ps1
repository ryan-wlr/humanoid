$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "start_everything.ps1"
if (-not (Test-Path $script)) {
  throw "Missing script: $script"
}

& $script @args

$marker = Join-Path $PSScriptRoot "start_everything.last_run.txt"
if (Test-Path $marker) {
  Write-Host "\n--- start_everything.last_run.txt ---" -ForegroundColor DarkCyan
  Get-Content $marker
} else {
  throw "Marker file was not created: $marker"
}
