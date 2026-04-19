#!/bin/bash
set -e

# =============================================================================
# Animagine MCP Docker Entrypoint
# =============================================================================
# This script runs on container startup to:
# 1. Ensure required directories exist
# 2. Verify/download the default model
# 3. Start the MCP server
# =============================================================================

echo "=== Animagine MCP Startup ==="

# -----------------------------------------------------------------------------
# 1. Ensure required directories exist
# -----------------------------------------------------------------------------
echo "Checking directories..."

mkdir -p /app/checkpoints
mkdir -p /app/loras
mkdir -p /app/outputs
mkdir -p /root/.cache/huggingface
mkdir -p /root/.cache/torch

echo "  ✓ /app/checkpoints"
echo "  ✓ /app/loras"
echo "  ✓ /app/outputs"
echo "  ✓ /root/.cache/huggingface"
echo "  ✓ /root/.cache/torch"

# -----------------------------------------------------------------------------
# 2. Verify/download Animagine XL 4.0 model
# -----------------------------------------------------------------------------
MODEL_ID="${MODEL_ID:-cagliostrolab/animagine-xl-4.0}"
SKIP_MODEL_DOWNLOAD="${SKIP_MODEL_DOWNLOAD:-false}"

if [ "$SKIP_MODEL_DOWNLOAD" = "true" ]; then
    echo "Skipping model download (SKIP_MODEL_DOWNLOAD=true)"
else
    echo "Verifying Animagine XL 4.0 model..."

    # Check if model exists in cache, download if not
    python -c "
from huggingface_hub import snapshot_download, try_to_load_from_cache
import os

model_id = '$MODEL_ID'
cache_dir = os.environ.get('HF_HOME', '/root/.cache/huggingface')

# Check if model config exists in cache
config_path = try_to_load_from_cache(model_id, 'model_index.json')

if config_path is None:
    print(f'  Downloading {model_id}...')
    print('  This may take a while on first run (~6GB)...')
    snapshot_download(model_id, cache_dir=cache_dir)
    print(f'  ✓ Model downloaded successfully')
else:
    print(f'  ✓ Model already cached')
"
fi

# -----------------------------------------------------------------------------
# 3. GPU Status Check
# -----------------------------------------------------------------------------
echo "Checking GPU status..."

python -c "
try:
    import torch
    if torch.cuda.is_available():
        print(f'  ✓ GPU Available: {torch.cuda.get_device_name(0)}')
        print(f'  ✓ CUDA Version: {torch.version.cuda}')
        print(f'  ✓ GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
    else:
        print('  ⚠ No GPU detected - running in CPU mode (slower)')
except Exception as e:
    print(f'  ⚠ GPU check skipped: {e}')
" || true

# -----------------------------------------------------------------------------
# 4. Start the application
# -----------------------------------------------------------------------------
echo "=== Starting Animagine MCP Server ==="
echo ""

# Execute the command passed to the container
exec "$@"
