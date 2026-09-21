# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`anime-diffusion-mcp` — a FastMCP server for anime image generation with Animagine XL 4.0. It exposes prompt validation/optimization and image generation (txt2img and img2img, with custom checkpoints and LoRAs) to AI agents over MCP (stdio). There is no REST API, REPL or Docker setup; the single entry point is the MCP server.

## Commands

```bash
python -m venv .venv
pip install -e .
anime-diffusion-mcp        # run the MCP server (stdio)
```

Quick import check without loading the model:

```bash
python -c "from anime_diffusion_mcp.server import mcp; print(mcp.name)"
python -c "from anime_diffusion_mcp.prompt import validate_prompt; print(validate_prompt('1girl, solo, masterpiece').model_dump())"
```

There is no test suite or lint config in the repo.

## Architecture

**`src/anime_diffusion_mcp/server.py`** — the 4 MCP tools: `validate_prompt`, `optimize_prompt`, `list_models`, `generate_image`. `generate_image` dispatches to img2img when `image_path` is given. Tool functions are thin wrappers; logic lives in the modules below.

**`prompt/`** — prompt processing pipeline:
- `tokenizer.py`: splits a prompt string into tags
- `classifier.py`: `TagCategory` enum + tag dictionaries; categorizes tags (quality, character, series, style, ...)
- `validator.py`: enforces Animagine rules (quality tags present and last, 8+ tags, character/series consistency, resolution risk)
- `optimizer.py`: reorders tags into canonical order and fills missing categories

**`diffusion/pipeline.py`** — `ImagePipeline`, a singleton via `get_pipeline()`. Handles checkpoint loading (HuggingFace default or local `.safetensors`), LoRA application (named adapters + `set_adapters`, replaced on every call), render-type validation (`gpu`/`cpu` vs `torch.cuda.is_available()`), and saving images with sidecar JSON metadata to `outputs/YYYY-MM-DD/`. Checkpoints are discovered from `checkpoints/`, LoRAs from `loras/` — both relative to the CWD. `_prepare()` is the shared setup for `generate()` and `generate_img2img()`.

**`contracts/`** — Pydantic schemas (`schemas.py`) and `ErrorCode` enum (`errors.py`) used by the prompt and diffusion modules.

## Conventions

- Base model id `cagliostrolab/animagine-xl-4.0` is intentionally kept; "Animagine XL" in docstrings refers to the model, not the project.
- When adding a capability, implement it in `prompt/` or `diffusion/` and expose it as a tool in `server.py`. Keep the tool count small.
- `diffusers` imports are lazy (inside methods) so the server starts fast and tools like `list_models` don't load torch models.
