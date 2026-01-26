$ErrorActionPreference = "Continue"

$cmd = @'
set -e;
BIN="/opt/ros/jazzy/bin/fast-discovery-server";
LOG="$HOME/.ros2ws_fastdds_11812.log";
if [ ! -x "$BIN" ]; then echo "MISSING_BIN" 1>&2; exit 10; fi;
nohup "$BIN" -i 0 -p 11812 >"$LOG" 2>&1 &
echo "STARTED_PID=$!";
echo "LOG=$LOG";
'@ -replace "\r\n", "\n"

Write-Host "Running in WSL: $cmd" -ForegroundColor DarkCyan
$out = & wsl.exe -d Ubuntu-24.04 -- bash -lc $cmd 2>&1
$code = $LASTEXITCODE

$out | ForEach-Object { Write-Host $_ }
Write-Host "ExitCode=$code" -ForegroundColor Cyan
exit $code
