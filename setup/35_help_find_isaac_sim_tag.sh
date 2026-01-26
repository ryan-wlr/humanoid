#!/usr/bin/env bash
set -euo pipefail

cat <<'TXT'
Isaac Sim Docker images are hosted on NVIDIA NGC.

What you need to do:

1) Create/login to your NVIDIA account.
2) In NGC, locate the Isaac Sim container and accept the EULA.
3) Copy the full image reference, which looks like:

   nvcr.io/nvidia/isaac-sim:<TAG>

Then export it in your shell:

   export ISAAC_SIM_BASE_IMAGE="nvcr.io/nvidia/isaac-sim:<TAG>"

After that, run:

   bash setup/40_build_image.sh

TXT