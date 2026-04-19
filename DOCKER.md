# Docker Setup for Animagine MCP

This guide explains how to build and run the Animagine MCP server using Docker.

## Prerequisites

### Basic Requirements
- **Docker**: [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose**: [Install Docker Compose](https://docs.docker.com/compose/install/)

### GPU Support (Recommended)
- **NVIDIA GPU**: GeForce RTX 30-series or newer (or equivalent)
- **CUDA Drivers**: [Install NVIDIA CUDA Drivers](https://www.nvidia.com/Download/driverDetails.html)
- **NVIDIA Container Runtime**: [Install nvidia-docker](https://github.com/NVIDIA/nvidia-docker)
- **Docker GPU Support**: [Configure Docker for GPU](https://docs.docker.com/config/containers/resource_constraints/#gpu)

### Verify GPU Setup

```bash
# Check NVIDIA driver
nvidia-smi

# Verify Docker GPU support
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi

# Check NVIDIA Container Runtime
docker info | grep nvidia
```

## Quick Start

### GPU Accelerated (Recommended - Default)

```bash
docker-compose up -d
```

This will:
1. Build optimized CUDA image with GPU acceleration
2. **Automatically download Animagine XL 4.0** (~6GB) during build
3. **Create required directories** (`checkpoints/`, `loras/`, `outputs/`) automatically
4. Start MCP server on `http://localhost:8000` with GPU support
5. Mount directories for models, LoRAs, and outputs
6. Enable GPU acceleration for image generation

> **First Build**: Takes 10-20 minutes (downloads model ~6GB). Subsequent builds use cached layers.

### CPU-Only (Fallback)

If GPU is unavailable, manually edit `docker-compose.yml` to remove:
```yaml
runtime: nvidia
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
```

Then run:
```bash
docker-compose up -d
```

## Automatic Features

The Docker container includes these automatic features on startup:

### 1. Directory Creation

The following directories are **automatically created** if they don't exist:
- `/app/checkpoints` - Model checkpoints
- `/app/loras` - LoRA modifiers
- `/app/outputs` - Generated images
- `/root/.cache/huggingface` - HuggingFace cache
- `/root/.cache/torch` - PyTorch cache

### 2. Model Download

**Animagine XL 4.0** is automatically downloaded:
- During Docker build (~6GB, cached in image)
- Verified on container startup

To skip model verification on startup:
```yaml
environment:
  SKIP_MODEL_DOWNLOAD: "true"
```

### 3. GPU Detection

On startup, the container checks GPU availability and displays:
```
=== Animagine MCP Startup ===
Checking directories...
  ✓ /app/checkpoints
  ✓ /app/loras
  ✓ /app/outputs
Verifying Animagine XL 4.0 model...
  ✓ Model already cached
Checking GPU status...
  ✓ GPU Available: NVIDIA GeForce RTX 3090
  ✓ CUDA Version: 12.1
  ✓ GPU Memory: 24.0GB
=== Starting Animagine MCP Server ===
```

## Directory Structure

The following directories are automatically created and mounted:

```
.
├── checkpoints/     # Model checkpoints (*.safetensors, *.ckpt)
├── loras/          # LoRA files (*.safetensors)
├── outputs/        # Generated images and metadata
└── docker volumes:
    ├── hf_cache/   # Hugging Face model cache
    └── torch_cache/ # PyTorch model cache
```

## Building Manually

To build the image without using compose:

```bash
docker build -t animagine-mcp:latest .
```

Then run:

```bash
docker run -it \
  -p 8000:8000 \
  -v $(pwd)/checkpoints:/app/checkpoints \
  -v $(pwd)/loras:/app/loras \
  -v $(pwd)/outputs:/app/outputs \
  animagine-mcp:latest
```

## Common Commands

### View Logs

```bash
docker-compose logs -f animagine-mcp
```

### Stop the Server

```bash
docker-compose down
```

### Stop and Remove Volumes

```bash
docker-compose down -v
```

### Rebuild the Image

```bash
docker-compose build --no-cache
```

### Shell Access

```bash
docker-compose exec animagine-mcp /bin/bash
```

## Configuration

### Environment Variables

Edit `docker-compose.yml` to customize, or pass via `docker-compose run -e VAR=value`:

| Variable | Description | Default |
|----------|-------------|---------|
| `SKIP_MODEL_DOWNLOAD` | Skip model download/verification on startup | `false` |
| `MODEL_ID` | HuggingFace model ID to download | `cagliostrolab/animagine-xl-4.0` |
| `HF_TOKEN` | HuggingFace access token (required for gated models) | _(unset)_ |
| `HF_HOME` | Hugging Face cache location | `/root/.cache/huggingface` |
| `TORCH_HOME` | PyTorch cache location | `/root/.cache/torch` |
| `CUDA_VISIBLE_DEVICES` | GPU device selection (e.g. `"0"`, `"0,1"`) | `"0"` |
| `PYTORCH_CUDA_ALLOC_CONF` | VRAM allocation strategy | `max_split_size_mb:512` |

> **Tip**: Set `SKIP_MODEL_DOWNLOAD=true` to skip the ~6GB download if the model is already cached in the mounted volume.

### Resource Limits

In `docker-compose.yml`, adjust under `deploy.resources`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

### Port Mapping

Change the exposed port in `docker-compose.yml`:

```yaml
ports:
  - "8000:8000"  # Change first 8000 to desired port
```

## GPU Acceleration Setup

### NVIDIA Container Runtime Installation

**Ubuntu/Debian:**
```bash
# Add NVIDIA repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-docker
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

**Windows with WSL2:**
```bash
# Install Docker Desktop with WSL2 backend
# Then in WSL2 terminal:
sudo apt-get update
sudo apt-get install -y nvidia-cuda-toolkit
```

**macOS with Apple Silicon:**
- Metal acceleration is not directly supported
- Use CPU-only or consider cloud GPU services

### Verify GPU in Container

```bash
# Check if GPU is accessible
docker-compose exec animagine-mcp nvidia-smi

# Check PyTorch GPU support
docker-compose exec animagine-mcp python -c "import torch; print(f'GPU Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

### Multi-GPU Support

Edit `docker-compose.yml` to use multiple GPUs:

```yaml
environment:
  CUDA_VISIBLE_DEVICES: "0,1,2,3"  # Use GPUs 0-3

deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['0', '1', '2', '3']
          capabilities: [gpu]
```

### GPU Memory Optimization

Set in `docker-compose.yml` environment:

```yaml
PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:512"  # Adjust if CUDA OOM errors
TORCH_CUDNN_BENCHMARK: "1"  # Enable auto-tuner for better performance
```

## Troubleshooting

### GPU Not Detected

**Check NVIDIA drivers:**
```bash
nvidia-smi  # Should show GPU info
```

**Verify container runtime:**
```bash
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi
```

**Check Docker daemon configuration:**
```bash
# Linux: Edit /etc/docker/daemon.json
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}

# Then restart Docker
sudo systemctl restart docker
```

**Container logs:**
```bash
docker-compose logs -f animagine-mcp
```

### CUDA Out of Memory (OOM)

Reduce model precision or batch size:
```yaml
environment:
  PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:256"  # Smaller chunks
```

Or use CPU-only fallback by removing GPU config.

### Slow GPU Performance

1. **Verify GPU is being used:**
   ```bash
   docker-compose exec animagine-mcp nvidia-smi  # Watch GPU-Util column
   ```

2. **Check GPU temperature:**
   ```bash
   docker-compose exec animagine-mcp nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader
   ```

3. **Enable GPU optimizations** (already in compose file):
   ```yaml
   TORCH_CUDNN_BENCHMARK: "1"
   TORCH_CUDNN_DETERMINISTIC: "0"
   ```

### Port Already in Use

```bash
# Change the port in docker-compose.yml
ports:
  - "8001:8000"

# Or kill the process using port 8000
lsof -i :8000
kill -9 <PID>
```

### Out of Memory

Increase Docker memory allocation:
```bash
# On Linux, edit daemon.json or use Docker Desktop settings
# Allocate more to Docker if not already at max
```

### Slow Image Generation

1. **Verify GPU acceleration is active:**
   ```bash
   docker-compose exec animagine-mcp nvidia-smi -l 1  # Watch GPU usage
   ```

2. **Pre-load models** using `load_checkpoint` tool

3. **Check disk space** for model cache:
   ```bash
   docker volume ls  # Find hf_cache and torch_cache
   docker volume inspect animagine_mcp_hf_cache
   ```

4. **Use GPU version** - ensure GPU acceleration is enabled

## Model Management

### Adding Checkpoints

Place `.safetensors` or `.ckpt` files in `./checkpoints/`:

```bash
cp model.safetensors ./checkpoints/
```

Then use `list_models()` to verify it's available.

### Adding LoRAs

Place LoRA files in `./loras/`:

```bash
cp lora_model.safetensors ./loras/
```

### Model Caching

Model downloads are cached in Docker volumes:

- `hf_cache`: Hugging Face models
- `torch_cache`: PyTorch models

This prevents re-downloading on container restart.

## Performance Tips

### GPU Optimization (Recommended for Production)

**Enable GPU acceleration for 10-50x faster generation:**

1. **Update NVIDIA drivers** to latest version:
   ```bash
   nvidia-smi  # Check current version
   # Visit https://www.nvidia.com/Download/driverDetails.html
   ```

2. **Monitor GPU usage during generation:**
   ```bash
   # In another terminal
   watch -n 1 nvidia-smi
   ```

3. **Enable all GPU optimizations** (defaults in docker-compose.yml):
   ```yaml
   TORCH_CUDNN_BENCHMARK: "1"      # Auto-tune for performance
   CUDA_LAUNCH_BLOCKING: "1"        # Better error messages
   PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:512"
   ```

4. **Pre-load models on startup:**
   ```bash
   # API call to load checkpoint before generation
   curl -X POST http://localhost:8000/call/load_checkpoint
   ```

### For Maximum GPU Performance

- Use RTX 30/40-series or A40 GPUs (CUDA compute capability 8.6+)
- Ensure adequate power supply (300W+ for high-end GPUs)
- Keep GPU at good thermals (< 80°C for longevity)
- Use PCIe Gen 4 slots if available

### For CPU-Only Systems (Fallback)

- Allocate maximum CPU cores
- Use swap memory if available
- Increase system memory allocation to Docker
- Set inference steps to 4-8 (faster but lower quality)
- Consider cloud GPU services for better performance

### Model Optimization

- **Pre-load checkpoints:** Reduces startup latency significantly
  ```bash
  docker-compose exec animagine-mcp python -c "
  from animagine_mcp.diffusion.pipeline import get_pipeline
  pipeline = get_pipeline()
  pipeline.load_checkpoint('default')  # Pre-loads Animagine XL
  "
  ```

- **Use TorchScript compilation** for repeated generation
- **Cache generated images** to reduce recomputation
- **Batch requests** when possible for better GPU utilization

### Measuring GPU Performance

```bash
# Monitor during generation
docker-compose exec animagine-mcp bash -c "
while true; do
  nvidia-smi --query-gpu=utilization.gpu,memory.used,power.draw \
    --format=csv,noheader,nounits
  sleep 1
done
"
```

**Healthy metrics:**
- GPU-Util: 95-100% (GPU is fully utilized)
- Memory: 70-90% of total (good cache usage)
- Power: 200-400W (depends on GPU model)

## Development

### Rebuild on Code Changes

```bash
docker-compose build --no-cache
docker-compose up -d
```

### View Real-Time Logs

```bash
docker-compose logs -f
```

### Debug Mode

Add `stdin_open: true` and `tty: true` to `docker-compose.yml`:

```yaml
stdin_open: true
tty: true
```

Then access with:

```bash
docker-compose exec animagine-mcp /bin/bash
```

## Production Considerations

- Use a reverse proxy (nginx/traefik) for load balancing
- Implement proper authentication for the MCP interface
- Set up monitoring and health checks
- Use persistent volumes for model cache
- Configure proper logging (already set to `json-file`)
- Consider using a Docker registry for image distribution

## Additional Resources

- [Animagine MCP Documentation](README.md)
- [FastMCP Documentation](https://github.com/jlouis/fastmcp)
- [Docker Documentation](https://docs.docker.com/)
- [NVIDIA Docker Documentation](https://github.com/NVIDIA/nvidia-docker)
