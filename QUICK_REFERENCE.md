# Quick Reference Card

## Endpoints at a Glance

```
BASE URL: http://localhost:8000/api/v1

┌─ PROMPT OPERATIONS ─────────────────────────────────────┐
│ POST /validate-prompt     Validate a prompt             │
│ POST /optimize-prompt     Optimize prompt tags          │
│ POST /explain-prompt      Explain what tags do          │
└─────────────────────────────────────────────────────────┘

┌─ MODEL MANAGEMENT ──────────────────────────────────────┐
│ GET  /models              List available models         │
│ POST /load-checkpoint     Load a checkpoint             │
│ POST /unload-loras        Remove LoRA weights           │
└─────────────────────────────────────────────────────────┘

┌─ IMAGE GENERATION ──────────────────────────────────────┐
│ POST /generate            Text-to-image (txt2img)       │
│ POST /generate-img2img    Image-to-image (img2img)      │
└─────────────────────────────────────────────────────────┘

┌─ UTILITIES ─────────────────────────────────────────────┐
│ GET  /health              Health check                  │
│ GET  /status              System status                 │
│ GET  /                    API info                      │
│ GET  /docs                Swagger UI docs              │
│ GET  /redoc               ReDoc docs                   │
└─────────────────────────────────────────────────────────┘
```

## Common Parameters

### Text Generation
```json
{
  "prompt": "1girl, blue hair, masterpiece",
  "steps": 28,
  "guidance_scale": 5.0,
  "seed": 12345,
  "width": 832,
  "height": 1216,
  "checkpoint": "custom_checkpoint.safetensors",
  "loras": ["custom_lora.safetensors"],
  "lora_scales": [0.8],
  "negative_prompt": "low quality, blurry"
}
```

### Fast Generation (LCM)
```json
{
  "prompt": "1girl, masterpiece",
  "loras": ["custom_lora.safetensors"],
  "steps": 4,
  "guidance_scale": 1.5
}
```

## Quick Start Commands

### Docker
```bash
docker-compose up -d          # Start
docker-compose logs -f        # Watch logs
curl http://localhost:8000    # Health check
```

### Local
```bash
pip install -e .              # Install dependencies
animagine-api                 # Start API server
curl http://localhost:8000    # Health check
```

### Validate Prompt
```bash
curl -X POST http://localhost:8000/api/v1/validate-prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "1girl, blue hair"}'
```

### List Models
```bash
curl http://localhost:8000/api/v1/models | python -m json.tool
```

### Generate Image
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "1girl, masterpiece", "steps": 28}'
```

### View API Docs
```
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc
```

## Python Quick Start

```python
import requests

API = "http://localhost:8000/api/v1"

# Generate image
response = requests.post(f"{API}/generate", json={
    "prompt": "1girl, blue hair, masterpiece",
    "steps": 28
})

result = response.json()
print(f"Image: {result['image_path']}")
```

## JavaScript Quick Start

```javascript
const API = "http://localhost:8000/api/v1";

// Generate image
const response = await fetch(`${API}/generate`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    prompt: "1girl, blue hair, masterpiece",
    steps: 28
  })
});

const result = await response.json();
console.log("Image:", result.image_path);
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Port 8000 in use | `animagine-api --port 8001` |
| Module not found | `pip install -e .` |
| CUDA OOM | Reduce steps/size or use LCM |
| Model not found | Check `/models` endpoint |
| Windows permission | Enable Developer Mode |

## Documentation Files

| File | Purpose |
|------|---------|
| README.md | Overview and quick start |
| API.md | Complete endpoint reference |
| INTEGRATION.md | Framework examples |
| ARCHITECTURE.md | System design diagrams |
| API_TROUBLESHOOTING.md | Error solutions |
| API_IMPLEMENTATION.md | What was added |
| API_SUPPORT_SUMMARY.md | Complete summary |
| CHECKLIST.md | Implementation checklist |

## File Locations

```
Project Root
├─ src/animagine_mcp/api.py        FastAPI server
├─ API.md                           Endpoint reference
├─ INTEGRATION.md                   Integration examples
├─ ARCHITECTURE.md                  System diagrams
├─ API_TROUBLESHOOTING.md           Error solutions
├─ API_IMPLEMENTATION.md            What was added
├─ API_SUPPORT_SUMMARY.md           Complete summary
├─ CHECKLIST.md                     Implementation checklist
├─ README.md                        Main documentation
├─ pyproject.toml                   Dependencies
├─ docker-compose.yml               Docker setup
├─ docker-compose.cpu.yml           CPU-only setup
└─ docker-compose.gpu.yml           GPU setup
```

## Entry Points

```bash
# REST API Server
animagine-api
uvicorn animagine_mcp.api:app --port 8000

# MCP Server (for Claude, Cursor, etc)
animagine-mcp

# Interactive REPL
animagine-repl
```

## Performance Tips

| Technique | Speedup | Trade-off |
|-----------|---------|-----------|
| Use LCM LoRA | 4-6x | Slightly lower quality |
| Reduce steps | 2x per 14 steps | Lower quality |
| Smaller resolution | Variable | Lower detail |
| Pre-load checkpoint | 10s saved | Memory usage |
| Batch requests | N/A | Sequential |

## Example Workflows

### Workflow 1: Simple Generation
```bash
# Just generate
curl -X POST http://localhost:8000/api/v1/generate \
  -d '{"prompt": "1girl, masterpiece"}'
```

### Workflow 2: Validated Generation
```bash
# 1. Validate
prompt=$(curl -s http://localhost:8000/api/v1/validate-prompt \
  -d '{"prompt": "1girl, blue hair"}' | jq -r '.canonically_ordered')

# 2. Generate
curl -X POST http://localhost:8000/api/v1/generate \
  -d "{\"prompt\": \"$prompt\"}"
```

### Workflow 3: Optimized Generation
```bash
# 1. Optimize
prompt=$(curl -s -X POST http://localhost:8000/api/v1/optimize-prompt \
  -d '{"description": "girl with blue hair"}' | jq -r '.optimized_prompt')

# 2. Generate
curl -X POST http://localhost:8000/api/v1/generate \
  -d "{\"prompt\": \"$prompt\"}"
```

### Workflow 4: Fast Generation (LCM)
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -d '{
    "prompt": "1girl, masterpiece",
    "loras": ["custom_lora.safetensors"],
    "steps": 4,
    "guidance_scale": 1.5
  }'
```

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Not found (model/file not found) |
| 500 | Server error (GPU OOM, CUDA error) |
| 503 | Service unavailable (GPU not ready) |

## Default Values

| Parameter | Default |
|-----------|---------|
| width | 832 |
| height | 1216 |
| steps | 28 |
| guidance_scale | 5.0 |
| strength (img2img) | 0.75 |
| seed | Random |
| checkpoint | Animagine XL 4.0 |
| lora_scales | 1.0 per LoRA |

## Recommended Prompts

```
Anime (Animagine optimized):
"1girl, blue hair, anime style, masterpiece, best quality"

Quality Tags (always include):
"masterpiece, best quality, official art"
```

## Monitoring

```bash
# Health check
curl http://localhost:8000/health

# Full status
curl http://localhost:8000/api/v1/status

# GPU info
nvidia-smi

# Logs
docker-compose logs -f

# API in action
watch -n 1 'curl -s http://localhost:8000/api/v1/status | jq'
```

---

**Need more help?**
- Full API docs: See [API.md](API.md)
- Integration examples: See [INTEGRATION.md](INTEGRATION.md)
- Troubleshooting: See [API_TROUBLESHOOTING.md](API_TROUBLESHOOTING.md)
- Architecture details: See [ARCHITECTURE.md](ARCHITECTURE.md)
