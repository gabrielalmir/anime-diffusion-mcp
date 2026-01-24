# GPU Acceleration Quick Setup Guide

This guide gets GPU acceleration working with your Animagine MCP container in minutes.

## 1. Prerequisites Check (2 minutes)

### Verify NVIDIA GPU

```bash
nvidia-smi
```

Expected output: GPU name, memory, driver version. If this fails:
- [Install NVIDIA drivers](https://www.nvidia.com/Download/driverDetails.html)
- Restart your computer

### Verify Docker with GPU Support

```bash
docker run --rm --runtime=nvidia --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi
```

Expected: GPU information displayed. If this fails:
- [Install nvidia-docker](https://github.com/NVIDIA/nvidia-docker)
- On Linux, edit `/etc/docker/daemon.json` and add:
  ```json
  {
    "runtimes": {
      "nvidia": {
        "path": "nvidia-container-runtime",
        "runtimeArgs": []
      }
    }
  }
  ```
- Restart Docker: `sudo systemctl restart docker` (Linux) or restart Docker Desktop (Windows/Mac)

## 2. Build GPU Image (5-10 minutes)

The Dockerfile is already optimized for GPU. Just build:

```bash
docker-compose build --no-cache
```

This will:
- Use CUDA 12.1 base image
- Install PyTorch with CUDA 12.1 support
- Configure all GPU optimizations

## 3. Start Container with GPU (1 minute)

```bash
docker-compose up -d
```

## 4. Verify GPU in Container

```bash
# Check NVIDIA tools
docker-compose exec animagine-mcp nvidia-smi

# Check PyTorch GPU access
docker-compose exec animagine-mcp python -c "
import torch
print(f'GPU Available: {torch.cuda.is_available()}')
print(f'GPU Count: {torch.cuda.device_count()}')
print(f'GPU Name: {torch.cuda.get_device_name(0)}')
print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
"
```

Expected output:
```
GPU Available: True
GPU Count: 1
GPU Name: NVIDIA GeForce RTX 3090
GPU Memory: 24.0GB
```

## 5. Test Image Generation

```bash
curl -X POST http://localhost:8000/call/generate_image \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "1girl, beautiful anime girl, masterpiece, best quality",
    "steps": 28,
    "guidance_scale": 5.0
  }'
```

Watch GPU usage in another terminal:

```bash
watch -n 1 nvidia-smi
```

During generation, you should see:
- GPU-Util: 95-100%
- Memory-Usage: 70-90%
- Process name: python

## Performance Monitoring

### Real-time GPU stats

```bash
docker-compose exec animagine-mcp nvidia-smi -l 1
```

### GPU temperature and power

```bash
docker-compose exec animagine-mcp nvidia-smi --query-gpu=temperature.gpu,power.draw --format=csv,noheader
```

### Python GPU usage details

```bash
docker-compose exec animagine-mcp python -c "
import torch
import torch.cuda as cuda

print(f'CUDA Devices: {cuda.device_count()}')
print(f'Current Device: {cuda.current_device()}')
print(f'Device Name: {cuda.get_device_name()}')
print(f'Device Capability: {cuda.get_device_capability()}')
print(f'Total Memory: {cuda.get_device_properties(0).total_memory / 1e9:.1f}GB')
print(f'Allocated: {cuda.memory_allocated(0) / 1e9:.1f}GB')
print(f'Cached: {cuda.memory_reserved(0) / 1e9:.1f}GB')
"
```

## Troubleshooting

### GPU not found in container

**Check if nvidia-runtime is set:**
```bash
docker inspect animagine-mcp-server | grep -i runtime
```

Should show: `"Runtime": "nvidia"`

**Fix:**
```bash
# Make sure docker-compose.yml has:
runtime: nvidia
```

### CUDA out of memory errors

Reduce model size or increase GPU memory limits:

```yaml
# In docker-compose.yml
environment:
  PYTORCH_CUDA_ALLOC_CONF: "max_split_size_mb:256"
```

### Slow performance (GPU not being used)

**Check GPU utilization:**
```bash
docker-compose exec animagine-mcp nvidia-smi -l 1
```

If GPU-Util is < 50%, GPU might not be configured correctly.

**Solution:**
1. Verify GPU drivers: `nvidia-smi` (on host)
2. Verify Docker config: See section 1
3. Restart container: `docker-compose down && docker-compose up -d`

### NVIDIA driver conflicts

```bash
# Remove conflicting NVIDIA packages
sudo apt-get autoremove --purge '*nvidia*'

# Install only driver (not toolkit)
sudo apt-get install nvidia-driver-XXX  # Replace XXX with your version
```

## Advanced: Multi-GPU Setup

### For systems with multiple GPUs

Edit `docker-compose.yml`:

```yaml
environment:
  CUDA_VISIBLE_DEVICES: "0,1,2,3"  # All GPUs visible

deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['0', '1', '2', '3']
          capabilities: [gpu]
```

Then test:
```bash
docker-compose exec animagine-mcp python -c "
import torch
print(f'GPUs Available: {torch.cuda.device_count()}')
for i in range(torch.cuda.device_count()):
    print(f'  GPU {i}: {torch.cuda.get_device_name(i)}')
"
```

## Performance Expectations

### RTX 30-series (RTX 3090, 3080, etc.)
- 512x512 image: 2-5 seconds
- 832x1216 image: 5-12 seconds
- 1024x1024 image: 8-15 seconds

### RTX 40-series (RTX 4090, etc.)
- 512x512 image: 1-3 seconds
- 832x1216 image: 3-8 seconds
- 1024x1024 image: 4-10 seconds

### A100/H100 (Enterprise)
- 832x1216 image: 1-4 seconds

### CPU-only (no GPU)
- 512x512 image: 30-120 seconds
- 832x1216 image: 60-300 seconds

## Next Steps

1. **Pre-load checkpoints** for faster inference:
   ```bash
   curl -X POST http://localhost:8000/call/load_checkpoint \
     -H "Content-Type: application/json" \
     -d '{"checkpoint": null}'
   ```

2. **Explore LoRA models** for style transfer:
   ```bash
   curl http://localhost:8000/call/list_models
   ```

3. **Batch multiple generations** to maximize GPU utilization

4. **Monitor container** for long-term stability:
   ```bash
   docker-compose logs -f --tail 100 animagine-mcp
   ```

## Support

For issues with:
- **NVIDIA drivers**: [NVIDIA Support](https://www.nvidia.com/support)
- **Docker GPU**: [Docker Docs](https://docs.docker.com/config/containers/resource_constraints/#gpu)
- **nvidia-docker**: [GitHub Issues](https://github.com/NVIDIA/nvidia-docker/issues)
- **Animagine MCP**: [Project Issues](https://github.com/yourproject/issues)
