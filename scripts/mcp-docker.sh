#!/usr/bin/env bash
# stdio entrypoint for MCP clients. NVIDIA GPU required. Never write to stdout.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${ANIME_DIFFUSION_IMAGE:-anime-diffusion-mcp:latest}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found. Install Docker and enable the WSL integration (Docker Desktop: Settings → Resources → WSL Integration)." >&2
  exit 1
fi

mkdir -p \
  "$ROOT/checkpoints" \
  "$ROOT/loras" \
  "$ROOT/outputs" \
  "$ROOT/.cache/huggingface" \
  "$ROOT/.cache/torch"

args=(
  run -i --rm
  --gpus all
  --user "$(id -u):$(id -g)"
  -e HOME=/tmp
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility
  -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
  -e HF_HOME=/cache/huggingface
  -e HUGGINGFACE_HUB_CACHE=/cache/huggingface/hub
  -e TORCH_HOME=/cache/torch
  -e PYTHONUNBUFFERED=1
  -e "CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}"
  -v "$ROOT/checkpoints:/app/checkpoints"
  -v "$ROOT/loras:/app/loras"
  -v "$ROOT/outputs:/app/outputs"
  -v "$ROOT/.cache/huggingface:/cache/huggingface"
  -v "$ROOT/.cache/torch:/cache/torch"
)

if [[ -n "${HF_TOKEN:-}" ]]; then
  args+=(-e "HF_TOKEN=${HF_TOKEN}")
fi

exec docker "${args[@]}" "$IMAGE"
