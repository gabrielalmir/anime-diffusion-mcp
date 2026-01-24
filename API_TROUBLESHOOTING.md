# API Troubleshooting Guide

## Common Issues and Solutions

### 1. API Server Won't Start

#### Error: `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Install missing dependencies
pip install -e .

# Or manually install
pip install fastapi uvicorn
```

#### Error: `Port 8000 already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process
kill <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows

# Or use a different port
uvicorn animagine_mcp.api:app --port 8001
```

#### Error: `Connection refused` when calling API

**Solution:**
```bash
# 1. Check if server is running
curl http://localhost:8000/health

# 2. If using Docker, check container is running
docker-compose ps

# 3. Start the server
docker-compose up -d  # Docker
animagine-api  # Local
```

---

### 2. Generation Errors

#### Error: `Failed to load checkpoint: [WinError 1314]` (Windows)

This is a Windows symlink permission issue. See [Windows Fixes](#windows-specific-fixes).

#### Error: `CUDA out of memory`

**Solution:**
```bash
# 1. Reduce image dimensions
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "...",
    "width": 512,
    "height": 768,
    "steps": 20
  }'

# 2. Reduce inference steps
# "steps": 20 instead of 28

# 3. Use LCM LoRA for much faster generation
"loras": ["custom_lora.safetensors"],
"steps": 4,
"guidance_scale": 1.5

# 4. Restart the server to clear cache
docker-compose restart  # Or restart process
```

#### Error: `Model file not found`

**Solution:**
```bash
# 1. Check available models
curl http://localhost:8000/api/v1/models | python -m json.tool

# 2. Add missing model to checkpoints/ or loras/
# Place .safetensors file in correct directory

# 3. Restart server to detect new models
```

#### Error: `Invalid image path` in img2img

**Solution:**
```bash
# Use absolute paths
curl -X POST http://localhost:8000/api/v1/generate-img2img \
  -H "Content-Type: application/json" \
  -d '{
    "image_path": "/app/outputs/2024-01-24/image_123.png",
    "prompt": "..."
  }'

# Or from Docker:
"image_path": "/path/inside/docker"
```

---

### 3. Validation and Optimization Issues

#### Error: `Either description or prompt must be provided`

**Solution:**
```bash
# provide at least one parameter
curl -X POST http://localhost:8000/api/v1/optimize-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "girl, blue hair"
  }'

# OR

curl -X POST http://localhost:8000/api/v1/optimize-prompt \
  -H "Content-Type: application/json" \
  -d '{
    "description": "a girl with blue hair"
  }'
```

#### Validation returns warnings but image quality is poor

**Solution:**
1. Check suggestions from validation response
2. Add quality tags: `masterpiece, best quality, official art`
3. Use optimize endpoint first
4. Add more descriptive tags

```bash
# Better workflow
curl http://localhost:8000/api/v1/optimize-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "girl, blue hair"}' \
  | jq '.optimized_prompt' | \
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d "@-"
```

---

### 4. Docker Issues

#### Docker image build is slow

**Solution:**
```bash
# Build in background
docker-compose build &

# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker-compose build

# Check progress
docker-compose build --progress=plain
```

#### Models not persisting after restart

**Solution:**
```bash
# Ensure volumes are properly mounted in docker-compose.yml
volumes:
  - ./checkpoints:/app/checkpoints:rw
  - ./loras:/app/loras:rw
  - ./outputs:/app/outputs:rw
  - hf_cache:/root/.cache/huggingface

# Check volume mounts
docker-compose exec animagine-mcp ls -la /app/checkpoints
```

#### GPU not detected in Docker

**Solution:**
```bash
# 1. Verify NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-runtime-ubuntu22.04 nvidia-smi

# 2. Check docker-compose.yml has runtime: nvidia
# 3. Check deploy.resources settings
# 4. Restart Docker daemon
sudo systemctl restart docker  # Linux
# Restart Docker Desktop  # Windows/Mac

# 5. Check compose file version
# Ensure version: "3.8" or higher for GPU support
```

---

### 5. Performance Issues

#### Generation is very slow (expected: 30-60 seconds)

**Solutions:**
1. **Use LCM LoRA** for 4-6x speedup:
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "...",
    "loras": ["custom_lora.safetensors"],
    "lora_scales": [1.0],
    "steps": 4,
    "guidance_scale": 1.5
  }'
```

2. **Reduce resolution**:
```json
{
  "width": 512,
  "height": 768,
  "steps": 20
}
```

3. **Pre-load checkpoint**:
```bash
# Load once, then generate multiple times
curl -X POST http://localhost:8000/api/v1/load-checkpoint \
  -d '{"checkpoint": "custom_checkpoint.safetensors"}'

# Then generate quickly
curl -X POST http://localhost:8000/api/v1/generate ...
```

#### API responses are slow

**Solutions:**
```bash
# 1. Check server logs
docker-compose logs -f animagine-mcp

# 2. Monitor GPU memory
nvidia-smi -l 1

# 3. Check system resources
top  # Linux/Mac
tasklist  # Windows

# 4. Restart if memory leak
docker-compose restart
```

---

### 6. Windows-Specific Fixes

#### Symlink Permission Error (WinError 1314)

**Solution 1: Enable Developer Mode** (easiest)
1. Settings → System → For developers
2. Toggle "Developer Mode" on
3. Restart Docker
4. Retry generation

**Solution 2: Run as Administrator**
1. Right-click Command Prompt/PowerShell
2. Select "Run as administrator"
3. Run Docker commands
4. Run API server

**Solution 3: Change Cache Location**
```bash
# Set environment variable
set HF_HOME=C:\tmp\huggingface

# Or in Python:
import os
os.environ['HF_HOME'] = 'C:\\tmp\\huggingface'
```

**Solution 4: Clear and Rebuild Cache**
```bash
# Remove cache
rmdir /s /q %USERPROFILE%\.cache\huggingface

# Restart and regenerate
```

---

### 7. Network/Connection Issues

#### `Connection refused` from another machine

**Solution:**
```bash
# Make sure API listens on all interfaces
uvicorn animagine_mcp.api:app --host 0.0.0.0 --port 8000

# In Docker, check port mapping
# Should have: ports: - "8000:8000"

# Check firewall
# Allow port 8000 in firewall settings
```

#### API works locally but not from Docker network

**Solution:**
```yaml
# docker-compose.yml
services:
  animagine-mcp:
    # ... existing config ...
    network_mode: bridge  # Ensure proper networking

  your-app:
    # Use service name as hostname
    environment:
      ANIMAGINE_API_URL: http://animagine-mcp:8000/api/v1
```

#### CORS errors from browser

**Solution:**
```python
# Add to api.py if needed:
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 8. Documentation and Help

#### API documentation not loading

**Solution:**
```bash
# Ensure server is running
curl http://localhost:8000/health

# Visit documentation
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
# http://localhost:8000/openapi.json (OpenAPI spec)
```

#### Can't remember endpoint names

**Solution:**
```bash
# Get endpoint list from server
curl http://localhost:8000/ | python -m json.tool

# Or visit /docs for interactive exploration
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("animagine_mcp")
logger.setLevel(logging.DEBUG)
```

### Check API Health

```bash
# Quick health check
curl http://localhost:8000/health

# Full status
curl http://localhost:8000/api/v1/status

# Pretty print
curl -s http://localhost:8000/api/v1/status | python -m json.tool
```

### Monitor GPU

```bash
# Continuous monitoring
nvidia-smi -l 1

# Just memory info
nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits
```

### Check Docker Logs

```bash
# Last 100 lines
docker-compose logs --tail 100

# Follow logs
docker-compose logs -f

# Specific service
docker-compose logs animagine-mcp

# With timestamps
docker-compose logs -f --timestamps
```

### Test Endpoint Connectivity

```bash
# Quick test all endpoints
for endpoint in validate-prompt models generate; do
  echo "Testing $endpoint..."
  curl -s http://localhost:8000/api/v1/$endpoint || echo "Failed"
done
```

---

## Getting Help

1. **Check API Documentation**: [API.md](API.md)
2. **See Integration Examples**: [INTEGRATION.md](INTEGRATION.md)
3. **Review Implementation Details**: [API_IMPLEMENTATION.md](API_IMPLEMENTATION.md)
4. **Check Main README**: [README.md](README.md)
5. **View Server Logs**: `docker-compose logs -f`
6. **Test with cURL**: Use examples in API.md

## Quick Reference

| Issue | Solution |
|-------|----------|
| Port in use | Change port: `--port 8001` |
| Module not found | Install deps: `pip install -e .` |
| CUDA OOM | Reduce size/steps, use LCM |
| Model not found | List models: `curl .../api/v1/models` |
| Windows symlink | Enable Developer Mode or run as admin |
| Slow generation | Use LCM LoRA or reduce resolution |
| CORS error | Add CORS middleware in api.py |
| GPU not detected | Check NVIDIA runtime and docker-compose |
