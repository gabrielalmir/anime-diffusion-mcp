# Docker MCP Connection Guide

This guide shows how to connect Claude Desktop or Cursor with the Animagine MCP server running in Docker.

## Prerequisites

- Docker installed and running
- `docker-compose` available
- Model image built: `docker-compose build`

---

## Option 1: Docker Compose + MCP (Recommended)

Best for development and long-running instances.

### Setup

1. **Start the Docker container:**
   ```bash
   docker-compose up -d
   ```

2. **Configure Claude Desktop/Cursor:**

   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

   **Linux**: `~/.config/Claude/claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "animagine-docker": {
         "command": "python",
         "args": ["-m", "animagine_mcp.api"],
         "env": {
           "HF_HOME": "/root/.cache/huggingface",
           "PYTHONUNBUFFERED": "1"
         },
         "disabled": false
       }
     }
   }
   ```

3. **Restart Claude Desktop/Cursor**

### Usage

In Claude, use the tools:
```
- validate_prompt
- optimize_prompt
- explain_prompt
- list_models
- load_checkpoint
- load_lora
- unload_loras
- generate_image
- generate_img2img
```

---

## Option 2: Docker Run (Ephemeral)

For temporary, isolated execution. Container stops after use.

### Setup

1. **Build the image:**
   ```bash
   DOCKER_BUILDKIT=1 docker-compose build
   ```

2. **Configure MCP (Claude Desktop/Cursor):**

   **Windows/PowerShell:**
   ```json
   {
     "mcpServers": {
       "animagine-docker": {
         "command": "docker",
         "args": [
           "run",
           "--rm",
           "--gpus", "all",
           "-v", "${USERPROFILE}/.cache/huggingface:/root/.cache/huggingface",
           "-v", "${PWD}/checkpoints:/app/checkpoints",
           "-v", "${PWD}/loras:/app/loras",
           "-v", "${PWD}/outputs:/app/outputs",
           "animagine-mcp:latest",
           "animagine-mcp"
         ],
         "env": {
           "CUDA_VISIBLE_DEVICES": "0"
         }
       }
     }
   }
   ```

   **macOS/Linux:**
   ```json
   {
     "mcpServers": {
       "animagine-docker": {
         "command": "docker",
         "args": [
           "run",
           "--rm",
           "--gpus", "all",
           "-v", "${HOME}/.cache/huggingface:/root/.cache/huggingface",
           "-v", "${PWD}/checkpoints:/app/checkpoints",
           "-v", "${PWD}/loras:/app/loras",
           "-v", "${PWD}/outputs:/app/outputs",
           "animagine-mcp:latest",
           "animagine-mcp"
         ],
         "env": {
           "CUDA_VISIBLE_DEVICES": "0"
         }
       }
     }
   }
   ```

3. **Restart Claude Desktop/Cursor**

### How It Works

- Each MCP call spins up a new Docker container
- Container automatically stops after request completes
- Models cached in `~/.cache/huggingface` volume
- Generated images saved to local `./outputs` directory

---

## Option 3: REST API (HTTP)

For remote connections or non-MCP tools.

### Setup

1. **Start Docker Compose:**
   ```bash
   docker-compose up -d
   ```

2. **Access via REST API:**
   ```bash
   curl http://localhost:8000/api/v1/models
   curl http://localhost:8000/docs  # Interactive API docs
   ```

3. **From Claude (using tools):**
   You can use the MCP interface to call the same endpoints.

---

## Option 4: CPU-Only Mode

For systems without NVIDIA GPU:

```bash
docker-compose -f docker-compose.cpu.yml up -d
```

---

## Volume Mounts Explained

| Path | Purpose | Notes |
|------|---------|-------|
| `./checkpoints` | Custom checkpoint files | Place `.safetensors` files here |
| `./loras` | LoRA weight files | Place `.safetensors` files here |
| `./outputs` | Generated images | Automatically created |
| `hf_cache` | HuggingFace model cache | Persistent across container restarts |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CUDA_VISIBLE_DEVICES` | `0` | GPU ID to use |
| `HF_HOME` | `/root/.cache/huggingface` | Model cache location |
| `TORCH_HOME` | `/root/.cache/torch` | PyTorch cache location |
| `PYTHONUNBUFFERED` | `1` | Real-time logging |

---

## Troubleshooting

### Container fails to start
```bash
docker-compose logs animagine-mcp
```

### GPU not detected
```bash
docker run --rm --gpus all nvidia/cuda:12.1.1-runtime-ubuntu22.04 nvidia-smi
```

### Model download takes forever
- First download is ~8GB (cached automatically)
- Check progress: `docker exec animagine-mcp-server ls -lh /root/.cache/huggingface`

### Permissions issues (Windows)
- Enable WSL 2 backend for Docker
- Run PowerShell as Administrator

### Out of memory
```bash
# Reduce resolution or steps
# Check available GPU memory:
docker exec animagine-mcp-server nvidia-smi
```

---

## Performance Tips

1. **Enable BuildKit for faster builds:**
   ```bash
   DOCKER_BUILDKIT=1 docker-compose build
   ```

2. **Use GPU volumes for speed:**
   - First-time model load: ~1-2 min
   - Subsequent loads: instant (cached)

3. **Batch operations:**
   - Load checkpoint once, generate multiple images
   - Avoid reloading same model repeatedly

4. **Monitor resource usage:**
   ```bash
   docker stats animagine-mcp-server
   ```

---

## Stopping/Cleaning Up

```bash
# Stop the service
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Remove unused Docker resources
docker system prune -a
```

---

## Advanced: Multi-GPU Setup

To use multiple GPUs, modify `docker-compose.yml`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['0', '1', '2']  # Use GPUs 0, 1, 2
          capabilities: [gpu]
```

Then set in MCP config:
```json
"env": {
  "CUDA_VISIBLE_DEVICES": "0,1,2"
}
```
