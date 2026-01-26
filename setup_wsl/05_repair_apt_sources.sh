#!/usr/bin/env bash
set -euo pipefail

# Repairs a common failure mode where a PGP key block was accidentally pasted
# into an APT sources file ("BEGIN PGP PUBLIC KEY BLOCK"), which breaks apt.

if [[ $EUID -eq 0 ]]; then
  echo "Please run as a normal user (script uses sudo)." >&2
  exit 1
fi

if [[ ! -d /etc/apt ]]; then
  echo "ERROR: /etc/apt not found. Are you running inside WSL Ubuntu?" >&2
  exit 1
fi

echo "Searching for accidentally pasted PGP blocks in APT source files..."
MATCHES=$(sudo grep -R "BEGIN PGP PUBLIC KEY BLOCK" -n /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null || true)

if [[ -z "${MATCHES}" ]]; then
  echo "No PGP blocks found in APT sources. Nothing to repair." 
  exit 0
fi

echo
echo "Found the following offending lines:" 
echo "${MATCHES}"
echo

echo "Backing up and removing offending files..."
TS=$(date +%Y%m%d_%H%M%S)

# Extract unique file paths from grep output
FILES=$(echo "${MATCHES}" | awk -F: '{print $1}' | sort -u)

for f in ${FILES}; do
  sudo cp -a "$f" "${f}.bak_${TS}"
  echo "Backed up: $f -> ${f}.bak_${TS}"

  # If it's a dedicated ROS file, remove it; otherwise comment out the PGP block lines.
  base=$(basename "$f")
  if [[ "$base" == "ros2.list" ]] || [[ "$base" == "ros2.sources" ]]; then
    sudo rm -f "$f"
    echo "Removed: $f"
  else
    sudo sed -i \
      -e 's/^-----BEGIN PGP PUBLIC KEY BLOCK-----/# (removed) BEGIN PGP PUBLIC KEY BLOCK/' \
      -e 's/^-----END PGP PUBLIC KEY BLOCK-----/# (removed) END PGP PUBLIC KEY BLOCK/' \
      "$f"
    echo "Commented PGP markers in: $f"
    echo "NOTE: You may still need to manually clean the rest of the key block in that file." 
  fi

done

echo
echo "Now run: sudo apt-get update"
