# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastMCP server for Animagine XL 4.0 image generation. Exposes prompt validation/optimization and image generation capabilities via both the MCP protocol (for AI agent integration) and a REST API.

## Commands

### Setup
```bash
python -m venv .venv
pip install -e ".[dev]"
pre-commit install
```

### Running
```bash
animagine-mcp     # MCP server
animagine-api     # REST API (FastAPI on port 8000, docs at /docs)
animagine-repl    # Interactive REPL for local testing
```

### Linting & Formatting
```bash
black src/
ruff check src/
ruff check --fix src/
```

### Tests
```bash
pytest tests/
pytest tests/ --cov=src/animagine_mcp
```

### Docker
```bash
docker-compose up -d                              # GPU (default)
docker-compose -f docker-compose.gpu.yml up -d   # Advanced GPU
docker-compose -f docker-compose.cpu.yml up -d   # CPU-only
docker-compose logs -f
docker-compose exec animagine-mcp bash
```

## Architecture

The project has three entry points backed by shared internals:

- **`server.py`** — FastMCP tool definitions (9 tools). This is the MCP interface.
- **`api.py`** — FastAPI endpoints (11 routes). Same functionality over HTTP.
- **`repl.py`** — Interactive CLI that wraps the same pipeline for local testing.

### Core Modules

**`src/animagine_mcp/prompt/`** — Prompt processing pipeline:
- `tokenizer.py`: Splits prompt string into tags
- `classifier.py`: Categorizes tags (quality, character, series, style, etc.)
- `validator.py`: Enforces Animagine rules RULE-01 through RULE-07
- `optimizer.py`: Reorders tags into canonical order, fills missing categories
- `explainer.py`: Generates per-tag explanations

**`src/animagine_mcp/diffusion/`** — Image generation:
- `pipeline.py`: `AnimaginePipeline` class — singleton via `get_pipeline()`. Handles checkpoint loading, LoRA application, GPU/CPU rendering, and saves images with JSON metadata to `outputs/`. Dynamically discovers checkpoints from `checkpoints/` and LoRAs from `loras/`.

**`src/animagine_mcp/contracts/`** — Shared schemas and errors:
- `schemas.py`: Pydantic models for all tool inputs/outputs
- `errors.py`: 18 standardized error codes used across both interfaces

### Dual Interface Pattern

Every capability is registered in both `server.py` (MCP) and `api.py` (REST). When adding a new feature, implement the logic in the appropriate `prompt/` or `diffusion/` module, then expose it in both interfaces.

### Render Type Validation

Image generation validates `render_type` (`gpu`/`cpu`) against detected hardware. GPU detection uses `torch.cuda.is_available()`. This is defined in `diffusion/pipeline.py` and enforced in both server and API layers.

### Model & Assets

- Base model: `cagliostrolab/animagine-xl-4.0` (downloaded from HuggingFace on first run)
- Custom checkpoints: drop `.safetensors` files into `checkpoints/` (auto-discovered)
- LoRAs: drop into `loras/` (auto-discovered)
- Generated images: saved to `outputs/` with sidecar `.json` metadata

### AI Agent Specifications

The numbered directories (`02-behavior/`, `03-contracts/`, `04-quality/`, `05-implementation/`) contain machine-readable specs for AI agent consumption — prompt rulebook, taxonomy, error handling contracts, quality guidelines. These inform how the prompt validation rules are implemented.
