#!/usr/bin/env bash
set -eEo pipefail

# Repo-local convenience wrapper for Windows Git Bash.
# Delegates to the main launcher located in your Windows home.

WIN_USER="ryan_"

is_wsl=false
if [[ -n "${WSL_DISTRO_NAME:-}" ]]; then
	is_wsl=true
elif [[ -r /proc/version ]] && grep -qi microsoft /proc/version; then
	is_wsl=true
fi

if $is_wsl; then
	target="/mnt/c/Users/${WIN_USER}/run_diff_drive_stack.sh"
else
	# MSYS/Git Bash style mount.
	target="/c/Users/${WIN_USER}/run_diff_drive_stack.sh"
fi

if [[ ! -f "$target" ]]; then
	echo "ERROR: Expected diff_drive launcher not found: $target" 1>&2
	echo "If your Windows username differs, update WIN_USER in ros2_ws/run_diff_drive_stack.sh" 1>&2
	exit 2
fi

exec "$target" "$@"
