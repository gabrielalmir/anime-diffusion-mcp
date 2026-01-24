# Docker Compose Reference Guide

Complete reference for all Docker Compose configurations available for Animagine MCP.

## Available Compose Files

### 1. `docker-compose.yml` (Recommended - GPU Default)

**Usage:**
```bash
docker-compose up -d
```

**Features:**
- ✅ GPU acceleration enabled (NVIDIA CUDA 12.1)
- ✅ Automatic GPU detection and configuration
- ✅ Optimized for production use
- ✅ PyTorch with CUDA support pre-installed
- ✅ cuDNN optimizations enabled
- ✅ Multi-GPU capable

**Best for:** Most systems with NVIDIA GPU

**GPU Acceleration:**
- Runtime: `nvidia`
- CUDA Version: 12.1
- Supported Architectures: 7.0-9.0 (GeForce/RTX/A-series)
- Memory Optimization: Enabled

### 2. `docker-compose.gpu.yml` (Advanced GPU)

**Usage:**
```bash
docker-compose -f docker-compose.gpu.yml up -d
```

**Features:**
- Same as above with enhanced monitoring
- Advanced GPU diagnostics
- Multi-GPU support template
- Performance profiling hooks
- Extended health checks

**Best for:** Production deployments, multi-GPU setups

**Additional Optimizations:**
```yaml
TORCH_CUDNN_BENCHMARK: "1"           # Auto-tune cuDNN
TORCH_CUDNN_DETERMINISTIC: "0"       # Allow non-deterministic
PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:512"
CUDA_DEVICE_ORDER: "PCI_BUS_ID"
```

### 3. `docker-compose.cpu.yml` (CPU Only)

**Usage:**
```bash
docker-compose -f docker-compose.cpu.yml up -d
```

**Features:**
- ✅ CPU-only execution (no GPU required)
- ✅ Optimized for multi-core systems
- ✅ Thread configuration for CPU cores
- ✅ Lower memory requirements possible
- ❌ No GPU acceleration

**Best for:** Development, testing, systems without NVIDIA GPU

**Thread Settings:**
- `OMP_NUM_THREADS`: Set to your CPU core count
- `TORCH_NUM_THREADS`: CPU parallelization
- Default: 8 cores (adjust for your system)

## Quick Selection Guide

```
┌─────────────────────────────────────────────────┐
│ Do you have NVIDIA GPU? (nvidia-smi shows GPU)  │
├─────────────────────────────────────────────────┤
│                                                 │
│  YES → docker-compose up -d                    │
│         (Use docker-compose.yml - BEST)        │
│                                                 │
│  NO  → docker-compose -f docker-compose.cpu.yml│
│        (Use CPU-only config - FALLBACK)        │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Configuration Comparison

| Feature | GPU (Default) | GPU (Advanced) | CPU |
|---------|:-------------:|:-------------:|:---:|
| GPU Acceleration | ✅ | ✅ | ❌ |
| CUDA Support | ✅ | ✅ | ❌ |
| Multi-GPU | ✅ | ✅ | ❌ |
| CPU Optimization | ⚠️  | ⚠️  | ✅ |
| Memory Efficient | ✅ | ✅ | ⚠️  |
| Production Ready | ✅ | ✅✅ | ✅ |
| Performance | 🚀🚀🚀 | 🚀🚀🚀 | 🐌 |

## Docker Image

### Base Images Used

**For GPU:**
- `nvidia/cuda:12.1.1-runtime-ubuntu22.04`
- Multi-stage build for optimized size
- PyTorch compiled for CUDA 12.1

**For CPU:**
- Same as GPU build (supports both)
- Dockerfile automatically configures for available GPU

### Image Size

- Compressed: ~5-6 GB
- Uncompressed: ~12-15 GB (includes models on first run)

### Build Time

- First build: 5-10 minutes (downloads dependencies)
- Rebuild (cached): 1-2 minutes

## Environment Variables

### GPU-Specific

```yaml
CUDA_VISIBLE_DEVICES: "0"                           # GPU device ID
CUDA_LAUNCH_BLOCKING: "1"                           # Better error msgs
TORCH_CUDA_ARCH_LIST: "7.0,7.5,8.0,8.6,8.9,9.0"   # GPU architectures
NVIDIA_VISIBLE_DEVICES: "all"                       # Container GPU access
NVIDIA_DRIVER_CAPABILITIES: "compute,utility"       # Required capabilities
TORCH_CUDNN_BENCHMARK: "1"                         # Auto-tune cuDNN
PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:512"  # Memory management
```

### Common

```yaml
PYTHONUNBUFFERED: "1"                               # Real-time output
PYTHONDONTWRITEBYTECODE: "1"                        # No .pyc files
HF_HOME: /root/.cache/huggingface                   # Model cache
TORCH_HOME: /root/.cache/torch                      # Torch cache
HF_HUB_DISABLE_TELEMETRY: "1"                      # Disable analytics
```

### CPU-Specific

```yaml
OMP_NUM_THREADS: "8"                                # OpenMP threads
OPENBLAS_NUM_THREADS: "8"                           # OpenBLAS threads
MKL_NUM_THREADS: "8"                                # MKL threads
TORCH_NUM_THREADS: "8"                              # PyTorch threads
```

## Volume Mounts

All configurations mount these volumes:

```yaml
volumes:
  ./checkpoints:/app/checkpoints         # Model checkpoints
  ./loras:/app/loras                     # LoRA modifiers
  ./outputs:/app/outputs                 # Generated images
  hf_cache:/root/.cache/huggingface      # HF model cache (persistent)
  torch_cache:/root/.cache/torch         # Torch cache (persistent)
```

**Docker Managed Volumes:**
- `hf_cache`: Persists Hugging Face downloads
- `torch_cache`: Persists PyTorch model cache

**Local Directories:**
- `checkpoints/`: Create for custom models
- `loras/`: Create for custom LoRAs
- `outputs/`: Auto-created for generated images

## Health Checks

### GPU (Default)

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import torch; assert torch.cuda.is_available()"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

Verifies:
- Python works
- PyTorch loads
- CUDA is available

### CPU

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

Verifies:
- Python works
- Container is responsive

## Port Configuration

**Default:** `8000:8000`

Change in any compose file:
```yaml
ports:
  - "8001:8000"  # Container port 8000 exposed as 8001
```

Or for multiple instances:
```yaml
# Instance 1
ports:
  - "8000:8000"

# Instance 2 (different compose file)
ports:
  - "8001:8000"
```

## Memory and CPU Limits

### GPU Configuration

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

- **Limits**: Hard cap on resources
- **Reservations**: Minimum guaranteed resources

### CPU Configuration

```yaml
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 8G
    reservations:
      cpus: '2'
      memory: 4G
```

Increase memory if models don't fit or generation is slow.

## Logging Configuration

All configurations use structured logging:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

- **JSON logging**: Machine-readable format
- **Max size**: 10MB per log file
- **Max files**: Keep last 3 rotations
- **Auto rotation**: Prevents disk space issues

View logs:
```bash
docker-compose logs -f --tail 100 animagine-mcp
```

## Restart Policy

All configurations use:
```yaml
restart: unless-stopped
```

Behavior:
- Automatically restarts on crash
- Respects manual `docker-compose down`
- Survives system reboot (with `docker run --restart unless-stopped`)

## Building and Running

### Build only (don't run)
```bash
docker-compose build
```

### Build and run
```bash
docker-compose up -d
```

### Rebuild (ignore cache)
```bash
docker-compose build --no-cache
```

### Stop services
```bash
docker-compose down
```

### Stop and remove volumes
```bash
docker-compose down -v
```

### View running services
```bash
docker-compose ps
```

### View logs
```bash
docker-compose logs -f animagine-mcp
```

## Multi-Container Setup

To run CPU and GPU versions simultaneously:

```bash
# GPU version on default port
docker-compose up -d

# CPU version on different port
docker-compose -f docker-compose.cpu.yml -p animagine-cpu up -d
```

Then access:
- GPU: `http://localhost:8000`
- CPU: Edit `docker-compose.cpu.yml` port to `8001:8000`

## Network Configuration

**Default:** Bridge network (isolated from host)

For other networks, add to compose file:
```yaml
networks:
  custom-net:
    driver: bridge

services:
  animagine-mcp:
    networks:
      - custom-net
```

## Docker Compose CLI Examples

```bash
# Start in background
docker-compose up -d

# Start and view logs
docker-compose up

# Stop all services
docker-compose stop

# Remove all services
docker-compose down

# View status
docker-compose ps

# View logs
docker-compose logs -f

# Execute command in running container
docker-compose exec animagine-mcp bash

# Scale service (if configured)
docker-compose up -d --scale animagine-mcp=2
```

## Common Issues and Solutions

### GPU not detected
```bash
# Verify host GPU
nvidia-smi

# Check Docker GPU support
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi
```

### Slow performance
- Verify GPU is being used: `docker-compose exec animagine-mcp nvidia-smi -l 1`
- Check resource limits don't restrict GPU

### Port conflicts
- Change port in compose: `ports: - "8001:8000"`
- Or kill process: `lsof -i :8000`

### Out of memory
- Increase memory in `deploy.resources.limits.memory`
- Reduce model size or inference steps

## Production Recommendations

1. **Use GPU compose** (`docker-compose.yml`) for best performance
2. **Monitor GPU** regularly with `nvidia-smi`
3. **Use health checks** - they're configured by default
4. **Set resource limits** to prevent system overload
5. **Use persistent volumes** for model cache
6. **Implement logging** - JSON driver is already configured
7. **Backup outputs** directory regularly
8. **Keep NVIDIA drivers updated**

## Additional Resources

- [Full Docker Documentation](DOCKER.md)
- [GPU Setup Quick Guide](GPU_SETUP.md)
- [Docker Compose Specification](https://docs.docker.com/compose/compose-file/)
- [NVIDIA Container Documentation](https://github.com/NVIDIA/nvidia-docker)
