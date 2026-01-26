param(
  [string]$WslDistro = "Ubuntu-24.04"
)

$ErrorActionPreference = "Stop"

$raw = & wsl.exe -d $WslDistro -- bash -lc "hostname -I 2>/dev/null || true"
$raw = ($raw | Out-String).Trim()

if (-not $raw) {
  throw "No IPs returned from WSL. Is the distro running?"
}

# Take first token
$ip = ($raw -split "\s+")[0]
if (-not $ip -or $ip -notmatch '^\d{1,3}(?:\.\d{1,3}){3}$') {
  throw "Failed to parse IPv4 from: '$raw'"
}

Write-Output $ip
