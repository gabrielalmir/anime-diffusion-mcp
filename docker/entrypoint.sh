#!/bin/sh
# Refuse to start unless the NVIDIA runtime exposed a GPU. Stderr only.
set -eu

# Native Linux (NVIDIA Container Toolkit) injects /dev/nvidia*.
# Docker Desktop on WSL2 injects /dev/dxg instead; nvidia-smi is the fallback
# when the runtime uses another device layout. Neither node exists without --gpus.
if [ -e /dev/nvidiactl ] || [ -e /dev/nvidia0 ] || [ -e /dev/dxg ]; then
  exec anime-diffusion-mcp
fi

if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
  exec anime-diffusion-mcp
fi

echo "anime-diffusion-mcp: NVIDIA GPU not visible in the container." >&2
echo "Start with --gpus all (NVIDIA Container Toolkit or Docker Desktop GPU)." >&2
exit 1
