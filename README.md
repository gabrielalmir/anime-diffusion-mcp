# Animagine MCP

FastMCP server for the **Animagine XL 4.0** image generation experience, providing prompt validation, optimization, explanation, and checkpoint/LoRA management tools.

> **For AI Agents**: This repository includes comprehensive markdown documentation in `02-behavior/`, `03-contracts/`, `04-quality/`, and `05-implementation/` directories. These files contain detailed specifications, behavior rules, prompt taxonomies, and implementation guides optimized for AI agent consumption. If you're building AI-powered workflows or need structured guidance for prompt engineering, check out these resources.

> **For Humans**: Welcome! A few friendly reminders:
> - **Do not commit AI agent files** (`.cursor/`, `.claude/`, `.copilot/`, etc.) — these are already in `.gitignore`
> - **Be respectful in discussions** — we're all here to learn and build together
> - **Help each other** — share your knowledge, ask questions, and contribute back
>
> Let's create something amazing together! 🎨

---

## Table of Contents

- [Overview](#overview)
- [Quick Start Guide](#quick-start-guide)
  - [Option 1: Docker (Recommended)](#option-1-docker-recommended)
  - [Option 1b: REST API Only](#option-1b-rest-api-only)
  - [Option 2: Local Installation](#option-2-local-installation)
  - [Option 3: Interactive REPL](#option-3-interactive-repl-testing)
  - [MCP Client Configuration](#mcp-client-configuration)
- [Core Tools](#core-tools)
- [Usage Examples](#usage-examples)
- [REST API](#rest-api)
- [Advanced Guide](#advanced-guide)
  - [GPU Acceleration](#gpu-acceleration)
  - [Docker Configuration](#docker-configuration)
  - [Model Management](#model-management)
  - [Environment Variables](#environment-variables)
  - [Performance Optimization](#performance-optimization)
- [AI Agent Resources](#ai-agent-resources)
- [Repository Layout](#repository-layout)
- [Contributors Guide](#contributors-guide)
  - [Development Setup](#development-setup)
  - [Code Style](#code-style)
  - [Pull Request Process](#pull-request-process)
  - [Testing Guidelines](#testing-guidelines)
- [Support](#support)
- [License](#license)

---

## Overview

Animagine MCP exposes powerful tools through **FastMCP** (MCP protocol) and **FastAPI** (REST API):
- **Prompt Tools**: `validate_prompt`, `optimize_prompt`, `explain_prompt`
- **Model Tools**: `list_models`, `load_checkpoint`, `unload_loras`
- **Generation Tools**: `generate_image`, `generate_image_from_image`

Key features:
- **Dual API support**: Use MCP protocol for AI agents or REST API for web/app integration
- Normalizes prompts for consistent structure, category coverage, and tag ordering
- Integrates with local checkpoint and LoRA assets
- GPU-accelerated image generation with CUDA support
- Docker-ready with comprehensive GPU configuration
- Interactive API documentation with Swagger UI

### Choose Your Interface

| Interface | Best For | Port |
|-----------|----------|------|
| **MCP Server** | Claude Desktop, Cursor, other MCP clients | stdio |
| **REST API** | Web applications, CLI tools, mobile apps | 8000 |
| **REPL** | Interactive testing and development | stdin/stdout |

> **Note**: This platform can generate NSFW material. Choosing to do so and owning the resulting content is the caller's responsibility.

---

## Quick Start Guide

### Option 1: Docker (Recommended)

The fastest way to get started with GPU acceleration.

#### What's Included

- **Automatic setup**: Directories (`checkpoints/`, `loras/`, `outputs/`) are created automatically
- **Pre-downloaded model**: Animagine XL 4.0 (~6GB) is downloaded during build
- **GPU acceleration**: CUDA 12.1 with optimized PyTorch
- **REST API**: FastAPI server on port 8000 with interactive documentation

#### Prerequisites

- Docker and Docker Compose installed
- NVIDIA GPU with drivers installed (verify with `nvidia-smi`)
- NVIDIA Container Toolkit ([installation guide](https://github.com/NVIDIA/nvidia-container-toolkit))
- ~15GB disk space (for Docker image + model)

#### Steps

**Step 1: Clone the repository**
```bash
git clone https://github.com/gabrielalmir/mcp-animaginexl.git
cd mcp-animaginexl
```

**Step 2: Build and start the container**
```bash
docker-compose up -d
```

> **Note**: First build downloads Animagine XL 4.0 (~6GB) and may take 10-20 minutes depending on your connection. Subsequent builds use cached layers.

**Step 3: Verify startup (watch logs)**
```bash
docker-compose logs -f
```

You should see:
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
=== Starting Animagine MCP Server ===
```

**Step 4: Access the services**

**REST API**:
- API Documentation: http://localhost:8000/docs (Swagger UI)
- Alternative docs: http://localhost:8000/redoc (ReDoc)
- Health check: `curl http://localhost:8000/health`

**MCP Server** (for Claude Desktop, Cursor, etc.):
- Stdio endpoint available to MCP clients
- See [MCP Client Configuration](#mcp-client-configuration)

#### Quick Docker Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start the server |
| `docker-compose down` | Stop the server |
| `docker-compose logs -f` | View logs |
| `docker-compose exec animagine-mcp bash` | Shell access |
| `docker-compose build --no-cache` | Rebuild from scratch |

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SKIP_MODEL_DOWNLOAD` | Skip model verification on startup | `false` |

---

### Option 1b: REST API Only

If you only want to use the REST API without MCP protocol support:

```bash
# Run the API server directly (requires local Python 3.11+)
pip install -e .
animagine-api
```

The API will be available at `http://localhost:8000` with full documentation at `/docs`.

---

### Option 2: Local Installation

For development or systems without Docker.

#### Prerequisites

- Python **>= 3.11**
- GPU with CUDA support (recommended)
- `git` and `pip`

#### Steps

**Step 1: Clone and create virtual environment**
```bash
git clone https://github.com/gabrielalmir/mcp-animaginexl.git
cd mcp-animaginexl
python -m venv .venv
```

**Step 2: Activate the virtual environment**

Windows:
```bash
.venv\Scripts\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

**Step 3: Install dependencies**
```bash
pip install -e .
```

**Step 4: Start the MCP server**
```bash
animagine-mcp
```

**Step 5: Verify it's running**

The server is now exposing tools via FastMCP at the default endpoint.

---

### Option 3: Interactive REPL (Testing)

Test MCP tools interactively without running the full server.

#### Quick Start

```bash
# From project root (no installation needed)
python repl.py

# Or if installed
animagine-repl
```

#### REPL Interface

```
╔═══════════════════════════════════════════════════════════════════╗
║                    Animagine MCP REPL                             ║
║                  Interactive Tool Testing                         ║
╠═══════════════════════════════════════════════════════════════════╣
║  Commands:                                                        ║
║    help              - Show help message                          ║
║    tools             - List available tools                       ║
║    tool <name>       - Show tool details                          ║
║    exit              - Exit the REPL                              ║
╚═══════════════════════════════════════════════════════════════════╝

animagine> validate_prompt("1girl, blue hair, masterpiece")
{
  "is_valid": true,
  "issues": [],
  "suggestions": [...]
}

animagine> optimize_prompt(description="anime girl in a garden")
{
  "optimized_prompt": "1girl, solo, garden, flowers, ..., masterpiece, best quality",
  "actions": [...]
}
```

#### CLI Options

```bash
python repl.py --list              # List all tools
python repl.py --tool validate     # Show tool details
python repl.py -e "list_models()"  # Execute single command
python repl.py --debug             # Enable debug mode
```

---

### MCP Client Configuration

To connect an MCP client (like Claude Desktop, VS Code, or other MCP-compatible tools) to this server, create a `.mcp.json` configuration file.

#### Example `.mcp.json`

**For local installation:**
```json
{
  "mcpServers": {
    "animagine": {
      "command": "animagine-mcp",
      "env": {}
    }
  }
}
```

**For development (running from source):**
```json
{
  "mcpServers": {
    "animagine": {
      "command": "python",
      "args": ["-m", "animagine_mcp.server"],
      "cwd": "/path/to/mcp-animaginexl",
      "env": {
        "PYTHONPATH": "/path/to/mcp-animaginexl/src"
      }
    }
  }
}
```

**For Docker:**
```json
{
  "mcpServers": {
    "animagine": {
      "command": "docker",
      "args": ["exec", "-i", "animagine-mcp-server", "animagine-mcp"],
      "env": {}
    }
  }
}
```

**Windows example:**
```json
{
  "mcpServers": {
    "animagine": {
      "command": "python",
      "args": ["-m", "animagine_mcp.server"],
      "cwd": "C:\\Users\\YourName\\Projects\\mcp-animaginexl",
      "env": {
        "PYTHONPATH": "C:\\Users\\YourName\\Projects\\mcp-animaginexl\\src"
      }
    }
  }
}
```

#### Configuration Options

| Field | Description |
|-------|-------------|
| `command` | Executable to run (`animagine-mcp`, `python`, or `docker`) |
| `args` | Command line arguments |
| `cwd` | Working directory (optional) |
| `env` | Environment variables (optional) |

#### Where to Place `.mcp.json`

Depending on your MCP client:

- **Claude Desktop**: `~/.config/claude/mcp.json` (Linux/Mac) or `%APPDATA%\Claude\mcp.json` (Windows)
- **VS Code**: Project root or workspace settings
- **Other clients**: Check client documentation

---

## Core Tools

The same powerful tools are available through **both** MCP protocol and REST API:

### Prompt Tools

| Tool | MCP Call | REST Endpoint | Description |
|------|----------|---------------|-------------|
| `validate_prompt` | `validate_prompt(...)` | `POST /api/v1/validate-prompt` | Validates prompt against Animagine XL rules |
| `optimize_prompt` | `optimize_prompt(...)` | `POST /api/v1/optimize-prompt` | Restructures and optimizes prompt tags |
| `explain_prompt` | `explain_prompt(...)` | `POST /api/v1/explain-prompt` | Explains each tag's category and effect |

### Model Tools

| Tool | MCP Call | REST Endpoint | Description |
|------|----------|---------------|-------------|
| `list_models` | `list_models()` | `GET /api/v1/models` | Lists available checkpoints and LoRAs |
| `load_checkpoint` | `load_checkpoint(...)` | `POST /api/v1/load-checkpoint` | Pre-loads a checkpoint to GPU memory |
| `unload_loras` | `unload_loras()` | `POST /api/v1/unload-loras` | Removes all LoRA weights from pipeline |

### Generation Tools

| Tool | MCP Call | REST Endpoint | Description |
|------|----------|---------------|-------------|
| `generate_image` | `generate_image(...)` | `POST /api/v1/generate` | Generates image from prompt |
| `generate_image_from_image` | `generate_image_from_image(...)` | `POST /api/v1/generate-img2img` | Image-to-image transformation |

### Using the REST API

For detailed REST API documentation, see **[API.md](API.md)** which includes:
- Full endpoint reference
- Request/response examples
- cURL examples
- Python client examples
- Performance tuning guide

**Quick start**:
```bash
# List available models
curl http://localhost:8000/api/v1/models

# Generate an image
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "masterpiece, best quality, anime girl",
    "steps": 28
  }'

# Interactive documentation
open http://localhost:8000/docs
```

---

## Usage Examples

### Example 1: Validate a Prompt

```python
# Validate before generation
result = validate_prompt(
    prompt="1girl, blue hair, school uniform",
    width=832,
    height=1216
)
print(result)  # Shows issues and suggestions
```

### Example 2: Optimize a Natural Language Description

```python
# Convert description to optimized tags
result = optimize_prompt(
    description="A beautiful anime girl with long silver hair standing in a flower field at sunset"
)
print(result["optimized_prompt"])
```

### Example 3: Generate an Image

```python
# Generate with default settings
result = generate_image(
    prompt="1girl, silver hair, flower field, sunset, masterpiece, best quality",
    steps=28,
    guidance_scale=5.0
)
print(f"Image saved to: {result['image_path']}")
```

### Example 4: Use Custom Checkpoint and LoRA

```python
# List available models first
models = list_models()
print(models["checkpoints"])
print(models["loras"])

# Generate with custom models
result = generate_image(
    prompt="1girl, anime style, masterpiece",
    checkpoint="custom_model.safetensors",
    loras=["style_lora.safetensors"],
    lora_scales=[0.8]
)
```

---

## REST API

For full REST API documentation with detailed examples, see **[API.md](API.md)**.

### Quick Reference

**Base URL**: `http://localhost:8000/api/v1`

**Interactive Documentation**: http://localhost:8000/docs

**Common Endpoints**:
- `POST /validate-prompt` - Validate a prompt
- `POST /optimize-prompt` - Optimize a prompt
- `POST /explain-prompt` - Explain prompt tags
- `GET /models` - List available models
- `POST /load-checkpoint` - Load a checkpoint
- `POST /generate` - Generate an image
- `POST /generate-img2img` - Transform an image

**Example**: Generate an image via REST API
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "masterpiece, best quality, anime girl, blue hair",
    "steps": 28,
    "guidance_scale": 5.0
  }'
```

---

## Advanced Guide

### GPU Acceleration

GPU acceleration provides **10-50x faster** generation compared to CPU.

#### Requirements

- NVIDIA GPU (GTX 1060 or newer recommended)
- CUDA drivers installed
- For Docker: NVIDIA Container Runtime

#### Verify GPU Setup

```bash
# Check NVIDIA driver
nvidia-smi

# Check PyTorch GPU support (in container or local env)
python -c "import torch; print(torch.cuda.is_available())"
```

#### GPU Performance Tips

1. **Pre-load checkpoints** to reduce first-generation latency:
   ```python
   load_checkpoint("default")  # Pre-loads Animagine XL 4.0
   ```

2. **Monitor GPU usage** during generation:
   ```bash
   watch -n 1 nvidia-smi
   ```

3. **Optimize memory** for large models:
   ```bash
   # Set in environment
   export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512"
   ```

See [GPU_SETUP.md](GPU_SETUP.md) for detailed GPU configuration.

---

### Docker Configuration

Three Docker Compose configurations are available:

| File | Description | Use Case |
|------|-------------|----------|
| `docker-compose.yml` | GPU-enabled (default) | Production with NVIDIA GPU |
| `docker-compose.gpu.yml` | Advanced GPU settings | Multi-GPU, profiling |
| `docker-compose.cpu.yml` | CPU-only fallback | Development, no GPU |

#### Switching Configurations

```bash
# GPU (default)
docker-compose up -d

# Advanced GPU
docker-compose -f docker-compose.gpu.yml up -d

# CPU-only
docker-compose -f docker-compose.cpu.yml up -d
```

#### Custom Port

Edit `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Change 8001 to desired port
```

#### Resource Limits

```yaml
deploy:
  resources:
    limits:
      memory: 8G  # Increase for larger models
```

See [DOCKER.md](DOCKER.md) for comprehensive Docker documentation.

---

### Model Management

#### Adding Checkpoints

Place `.safetensors` or `.ckpt` files in `./checkpoints/`:
```bash
cp my_model.safetensors ./checkpoints/
```

#### Adding LoRAs

Place LoRA files in `./loras/`:
```bash
cp my_lora.safetensors ./loras/
```

#### Verifying Models

```python
models = list_models()
print("Checkpoints:", models["checkpoints"])
print("LoRAs:", models["loras"])
print("Currently loaded:", models["currently_loaded"])
```

---

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CUDA_VISIBLE_DEVICES` | GPU device ID(s) | `0` |
| `TORCH_CUDNN_BENCHMARK` | Enable cuDNN auto-tuner | `1` |
| `PYTORCH_CUDA_ALLOC_CONF` | Memory allocation config | `max_split_size_mb:512` |
| `HF_HOME` | Hugging Face cache directory | `~/.cache/huggingface` |
| `HF_HUB_DISABLE_TELEMETRY` | Disable HF telemetry | `1` |

#### Setting Variables

Local:
```bash
export CUDA_VISIBLE_DEVICES=0
animagine-mcp
```

Docker (in `docker-compose.yml`):
```yaml
environment:
  CUDA_VISIBLE_DEVICES: "0,1"  # Use GPUs 0 and 1
```

---

### Performance Optimization

#### Recommended Settings by GPU

| GPU | VRAM | Recommended Steps | Batch Size |
|-----|------|-------------------|------------|
| RTX 3060 | 12GB | 28 | 1 |
| RTX 3080 | 10GB | 28 | 1 |
| RTX 3090 | 24GB | 28-50 | 1-2 |
| RTX 4090 | 24GB | 28-50 | 2-4 |
| A100 | 40GB+ | 50+ | 4+ |

#### Speed vs Quality Trade-offs

| Setting | Speed | Quality |
|---------|-------|---------|
| `steps=20` | Fast | Good |
| `steps=28` | Balanced | Great |
| `steps=50` | Slow | Excellent |

#### Using LCM LoRA for Speed

```python
# 4-8x faster generation with LCM
result = generate_image(
    prompt="1girl, masterpiece",
    loras=["custom_lora.safetensors"],
    steps=8,  # Reduced from 28
    guidance_scale=1.5  # Reduced from 5.0
)
```

---

## AI Agent Resources

This repository includes comprehensive documentation optimized for AI agents and automated workflows.

### Documentation Structure

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `02-behavior/` | Model behavior specifications | `model-behavior-spec.md`, `prompt-rulebook.md`, `prompt-taxonomy.yaml` |
| `03-contracts/` | Interface contracts and schemas | `mcp-interface-contract.md`, `config-defaults-spec.md`, `error-handling-spec.md` |
| `04-quality/` | Quality guidelines and strategies | `quality-evaluation-guide.md`, `negative-prompt-strategy.md`, `prompt-cookbook.md` |
| `05-implementation/` | Implementation guides | `implementation-guide.md`, `mcp-tooling-notes.md` |

### For AI Agent Developers

These resources are designed for:

- **Prompt Engineering**: Detailed taxonomy and rules for Animagine XL 4.0 prompts
- **Automated Pipelines**: Structured contracts for integrating with CI/CD or batch processing
- **Quality Assurance**: Evaluation criteria and negative prompt strategies
- **MCP Integration**: Interface specifications for building MCP-compatible clients

### Quick Links

```bash
# View behavior specifications
cat 02-behavior/model-behavior-spec.md

# View prompt rules and taxonomy
cat 02-behavior/prompt-rulebook.md
cat 02-behavior/prompt-taxonomy.yaml

# View MCP interface contract
cat 03-contracts/mcp-interface-contract.md

# View quality guidelines
cat 04-quality/prompt-cookbook.md
```

### Using with AI Coding Assistants

When using AI coding assistants (Claude, Cursor, Copilot, etc.), you can reference these docs:

```
"Read 02-behavior/prompt-rulebook.md and help me create a valid Animagine prompt"
"Based on 03-contracts/mcp-interface-contract.md, implement a client for this MCP"
"Use 04-quality/negative-prompt-strategy.md to improve my negative prompts"
```

---

## Repository Layout

```
mcp-animaginexl/
├── src/animagine_mcp/          # Core package
│   ├── contracts/              # Data schemas and errors
│   ├── diffusion/              # Diffusion pipeline wrapper
│   ├── prompt/                 # Prompt processing tools
│   ├── server.py               # FastMCP server definition
│   └── repl.py                 # Interactive REPL module
├── checkpoints/                # Model checkpoints (.safetensors) [auto-created]
├── loras/                      # LoRA modifiers [auto-created]
├── outputs/                    # Generated images [auto-created]
├── 02-behavior/                # Behavior specifications
├── 03-contracts/               # Interface contracts
├── 04-quality/                 # Quality guidelines
├── 05-implementation/          # Implementation notes
├── .mcp.json.example           # MCP client config template
├── Dockerfile                  # GPU-optimized container
├── docker-entrypoint.sh        # Container startup script
├── docker-compose.yml          # Default GPU config
├── docker-compose.gpu.yml      # Advanced GPU config
├── docker-compose.cpu.yml      # CPU-only fallback
├── repl.py                     # Interactive REPL (run directly)
├── pyproject.toml              # Project metadata
└── README.md                   # This file
```

---

## Contributors Guide

We welcome contributions! Here's how to get started.

### Development Setup

**Step 1: Fork and clone**
```bash
git clone https://github.com/YOUR_USERNAME/mcp-animaginexl.git
cd mcp-animaginexl
```

**Step 2: Create development environment**
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

**Step 3: Install with development dependencies**
```bash
pip install -e ".[dev]"
```

**Step 4: Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

---

### Code Style

We follow these conventions:

#### Python Style
- **Formatter**: `black` with default settings
- **Linter**: `ruff` for fast linting
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for all public APIs

#### Run Formatting
```bash
# Format code
black src/

# Lint code
ruff check src/

# Fix auto-fixable issues
ruff check --fix src/
```

#### Pre-commit (Recommended)
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

---

### Pull Request Process

#### 1. Before Submitting

- [ ] Code follows the style guide
- [ ] Tests pass locally
- [ ] Documentation updated (if applicable)
- [ ] Commit messages are clear and descriptive

#### 2. PR Template

Use this template for your PR description:

```markdown
## Summary
Brief description of changes.

## Changes
- Change 1
- Change 2

## Testing
How was this tested?

## Related Issues
Fixes #123
```

#### 3. Review Process

1. Submit PR to `main` branch
2. Automated checks run (linting, tests)
3. Maintainer reviews code
4. Address feedback if any
5. PR merged after approval

#### 4. Commit Message Format

```
type: short description

Longer description if needed.

Fixes #123
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat: add batch generation support
fix: resolve CUDA OOM error with large images
docs: update GPU setup instructions
```

---

### Testing Guidelines

#### Running Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/animagine_mcp

# Run specific test file
pytest tests/test_prompt.py
```

#### Writing Tests

```python
# tests/test_prompt.py
import pytest
from animagine_mcp.prompt import validate_prompt

def test_validate_prompt_basic():
    """Test basic prompt validation."""
    result = validate_prompt("1girl, blue hair, masterpiece")
    assert result.is_valid
    assert len(result.issues) == 0

def test_validate_prompt_missing_quality():
    """Test validation catches missing quality tags."""
    result = validate_prompt("1girl, blue hair")
    assert not result.is_valid
    assert any("quality" in issue.lower() for issue in result.issues)
```

#### Test Categories

| Category | Description | Location |
|----------|-------------|----------|
| Unit | Individual functions | `tests/unit/` |
| Integration | Component interaction | `tests/integration/` |
| E2E | Full workflow | `tests/e2e/` |

---

### Areas for Contribution

Looking for something to work on? Here are some areas:

#### Good First Issues
- Documentation improvements
- Adding test coverage
- Fixing typos or clarifying comments

#### Feature Ideas
- Additional prompt optimization strategies
- New LoRA management features
- Performance benchmarking tools
- Web UI frontend

#### Documentation
- Tutorials for specific use cases
- Video walkthroughs
- Translated documentation

---

## Support

### Getting Help

1. **Check existing issues**: Search [GitHub Issues](https://github.com/gabrielalmir/mcp-animaginexl/issues)
2. **Read documentation**: Check `DOCKER.md`, `GPU_SETUP.md`, and this README
3. **Open new issue**: Include:
   - Description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System info (OS, GPU, Python version)
   - Relevant logs (omit sensitive content)

### Community

- GitHub Discussions for questions
- Issues for bugs and feature requests

---

## License

This project is licensed under the terms specified in [LICENSE](LICENSE).

---

## Acknowledgments

- [Animagine XL](https://huggingface.co/cagliostrolab/animagine-xl-4.0) by Cagliostro Lab
- [FastMCP](https://github.com/jlouis/fastmcp) for the MCP framework
- [Diffusers](https://github.com/huggingface/diffusers) by Hugging Face
- All contributors and community members
