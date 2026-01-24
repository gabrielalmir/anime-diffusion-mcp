# Multi-stage build for GPU acceleration
# Stage 1: Builder with CUDA support
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 as builder

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install Python 3.11 and build dependencies in single layer for better caching
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    tzdata \
    && ln -fs /usr/share/zoneinfo/UTC /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set python3.11 as default python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Upgrade pip - cache this layer
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

WORKDIR /app

# Copy only pyproject.toml first for better caching of dependencies
COPY pyproject.toml ./

# Install dependencies (this layer caches if pyproject.toml doesn't change)
RUN pip install --no-cache-dir \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 && \
    pip install --no-cache-dir -e . --no-deps

# Now copy source and other files (won't invalidate dependency cache if only source changes)
COPY src ./src
COPY README.md LICENSE ./

# Stage 2: Runtime with CUDA support
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install Python 3.11 runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    tzdata \
    && ln -fs /usr/share/zoneinfo/UTC /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && add-apt-repository ppa:deadsnakes/ppa -y \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

# Set python3.11 as default python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Set working directory
WORKDIR /app

# Copy installed packages from builder (lightweight - no models)
COPY --from=builder /usr/local/lib/python3.11/dist-packages /usr/local/lib/python3.11/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project files
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

# Create directories for models and outputs
RUN mkdir -p /app/checkpoints /app/loras /app/outputs

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set environment variables for GPU acceleration
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CUDA_VISIBLE_DEVICES=0
ENV CUDA_LAUNCH_BLOCKING=1
ENV TORCH_CUDA_ARCH_LIST=7.0,7.5,8.0,8.6,8.9,9.0
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV HF_HOME=/root/.cache/huggingface
ENV TORCH_HOME=/root/.cache/torch

# Expose port for MCP server
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import torch; assert torch.cuda.is_available()" || exit 1

# Use entrypoint to ensure directories exist
ENTRYPOINT ["docker-entrypoint.sh"]

# Run the MCP server
CMD ["animagine-mcp"]
