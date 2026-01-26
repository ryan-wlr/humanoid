param(
  [string]$DomainId = "0",
  [string]$DiscoveryServer = "192.168.1.200:11812"
)

$vars = @{
  ROS_DOMAIN_ID              = $DomainId
  ROS_LOCALHOST_ONLY         = "0"
  ROS_DISTRO                 = "humble"
  RMW_IMPLEMENTATION         = "rmw_fastrtps_cpp"
  FASTDDS_BUILTIN_TRANSPORTS = "UDPv4"
  ROS_DISCOVERY_SERVER       = $DiscoveryServer
}

foreach ($k in $vars.Keys) {
  [Environment]::SetEnvironmentVariable($k, $vars[$k], "User")
}

Write-Host "Set USER environment variables:" -ForegroundColor Cyan
$vars.GetEnumerator() | Sort-Object Name | ForEach-Object { Write-Host ("  {0}={1}" -f $_.Name, $_.Value) }

Write-Host "\nClose and re-open Isaac Sim after this so it picks them up." -ForegroundColor Yellow
