# syntax=docker/dockerfile:1
# Slim Python + the CUDA 12.4 PyTorch wheel (the wheel ships the CUDA runtime).
# Host still needs an NVIDIA driver and --gpus all so the driver libs are injected.
# Animagine weights are not baked in; they land in the mounted HF cache.

FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    HF_HOME=/cache/huggingface \
    HUGGINGFACE_HUB_CACHE=/cache/huggingface/hub \
    TORCH_HOME=/cache/torch

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /app/checkpoints /app/loras /app/outputs /cache/huggingface /cache/torch \
    && chmod 777 /app/checkpoints /app/loras /app/outputs /cache /cache/huggingface /cache/torch

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY docker/entrypoint.sh /entrypoint.sh

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install torch --index-url https://download.pytorch.org/whl/cu124 \
    && pip install -e . \
    && python -c "import torch; assert torch.version.cuda, 'CUDA torch wheel was not installed'" \
    && chmod +x /entrypoint.sh

# stdio MCP: do not allocate a TTY. Logs must stay on stderr.
ENTRYPOINT ["/entrypoint.sh"]
