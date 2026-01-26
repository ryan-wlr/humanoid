param(
  [string]$IsaacRoot = "C:\\isaacsim",
  [string]$RuleNamePrefix = "Isaac Sim ROS2 (Fast DDS)"
)

$ErrorActionPreference = "Stop"

function Assert-Admin {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $isAdmin) {
    throw "This script must be run from an elevated PowerShell (Run as Administrator)."
  }
}

function Add-FirewallRuleIfMissing {
  param(
    [string]$DisplayName,
    [ValidateSet('Inbound','Outbound')] [string]$Direction,
    [string]$Program,
    [ValidateSet('UDP','TCP')] [string]$Protocol = 'UDP'
  )

  $existing = Get-NetFirewallRule -DisplayName $DisplayName -ErrorAction SilentlyContinue
  if ($existing) {
    Write-Host "Already exists: $DisplayName" -ForegroundColor DarkCyan
    return
  }

  $params = @{
    DisplayName = $DisplayName
    Direction   = $Direction
    Action      = 'Allow'
    Program     = $Program
    Protocol    = $Protocol
    Profile     = 'Any'
  }
  New-NetFirewallRule @params | Out-Null

  Write-Host "Added: $DisplayName" -ForegroundColor Green
}

Assert-Admin

$kitExe = Join-Path $IsaacRoot "kit\\kit.exe"
if (-not (Test-Path $kitExe)) {
  throw "kit.exe not found at: $kitExe (check -IsaacRoot)"
}

$kitPythonExe = Join-Path $IsaacRoot "kit\\python\\kit.exe"

Write-Host "Configuring Windows Firewall rules for Isaac Sim ROS 2 bridge..." -ForegroundColor Cyan
Write-Host "  kit.exe: $kitExe" -ForegroundColor DarkCyan
if (Test-Path $kitPythonExe) {
  Write-Host "  kit (python): $kitPythonExe" -ForegroundColor DarkCyan
}

# Most common blocker for Windows<->WSL Fast DDS Discovery Server setups:
# Windows Firewall blocks inbound UDP replies from the WSL discovery server.
# Allowing inbound UDP for kit.exe is the most robust fix (DDS uses ephemeral ports).
Add-FirewallRuleIfMissing -DisplayName "$RuleNamePrefix - Allow UDP Inbound (kit.exe)" -Direction Inbound -Program $kitExe -Protocol UDP

# Outbound is usually allowed by default, but keeping it explicit helps on locked-down machines.
Add-FirewallRuleIfMissing -DisplayName "$RuleNamePrefix - Allow UDP Outbound (kit.exe)" -Direction Outbound -Program $kitExe -Protocol UDP

# If you launch ROS 2 nodes via C:\isaacsim\python.bat, the executable is kit\python\kit.exe.
# It needs the same firewall allowances as the main kit.exe.
if (Test-Path $kitPythonExe) {
  Add-FirewallRuleIfMissing -DisplayName "$RuleNamePrefix - Allow UDP Inbound (kit (python).exe)" -Direction Inbound -Program $kitPythonExe -Protocol UDP
  Add-FirewallRuleIfMissing -DisplayName "$RuleNamePrefix - Allow UDP Outbound (kit (python).exe)" -Direction Outbound -Program $kitPythonExe -Protocol UDP
}

Write-Host "Done." -ForegroundColor Green
