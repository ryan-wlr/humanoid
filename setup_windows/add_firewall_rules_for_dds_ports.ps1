param(
  [string]$RuleNamePrefix = "ROS 2 / DDS Ports",
  [string]$PortRange = "7400-7600",
  [ValidateSet('Any','Private','Public','Domain')] [string]$Profile = "Any"
)

$ErrorActionPreference = "Stop"

function Assert-Admin {
  $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $isAdmin) {
    throw "This script must be run from an elevated PowerShell (Run as Administrator)."
  }
}

function Add-RuleIfMissing {
  param(
    [string]$DisplayName,
    [ValidateSet('Inbound','Outbound')] [string]$Direction,
    [string]$LocalPort,
    [ValidateSet('UDP','TCP')] [string]$Protocol = 'UDP'
  )

  $existing = Get-NetFirewallRule -DisplayName $DisplayName -ErrorAction SilentlyContinue
  if ($existing) {
    Write-Host "Already exists: $DisplayName" -ForegroundColor DarkCyan
    return
  }

  New-NetFirewallRule -DisplayName $DisplayName -Direction $Direction -Action Allow -Protocol $Protocol -LocalPort $LocalPort -Profile $Profile | Out-Null
  Write-Host "Added: $DisplayName" -ForegroundColor Green
}

Assert-Admin

Write-Host "Adding firewall rules for DDS/RTPS ports..." -ForegroundColor Cyan
Write-Host "  PortRange: $PortRange" -ForegroundColor DarkCyan
Write-Host "  Profile:   $Profile" -ForegroundColor DarkCyan

Add-RuleIfMissing -DisplayName "$RuleNamePrefix - Allow UDP Inbound ($PortRange)" -Direction Inbound -LocalPort $PortRange -Protocol UDP
Add-RuleIfMissing -DisplayName "$RuleNamePrefix - Allow UDP Outbound ($PortRange)" -Direction Outbound -LocalPort $PortRange -Protocol UDP

Write-Host "Done." -ForegroundColor Green
