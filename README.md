# anime-diffusion-mcp

MCP server for anime image generation with [Animagine XL 4.0](https://huggingface.co/cagliostrolab/animagine-xl-4.0).
Gives AI agents four tools: validate and optimize Danbooru-style prompts, list local models, and generate images (text-to-image or image-to-image) with custom checkpoints and LoRAs.

## Requirements

- Python 3.11+
- NVIDIA GPU with ~7 GB VRAM recommended (CPU works, but is very slow)
- ~7 GB of disk for the base model (downloaded from HuggingFace on first generation)

## Installation

```bash
git clone https://github.com/gabrielalmir/anime-diffusion-mcp.git
cd anime-diffusion-mcp
python -m venv .venv
# Windows: .venv\Scripts\activate  |  Linux/macOS: source .venv/bin/activate
pip install -e .
```

For CUDA, install the matching PyTorch build first (see https://pytorch.org/get-started/locally/), then `pip install -e .`.

## Docker

GPU only. The image is a slim Python base plus the CUDA 12.4 PyTorch wheel (the wheel already contains the CUDA runtime). It always starts with `--gpus all` and exits if no GPU device is visible (`/dev/nvidia*` on Linux, `/dev/dxg` on Docker Desktop / WSL2) — there is no CPU fallback. The ~7 GB Animagine weights are **not** in the image: the first generation downloads them into `.cache/huggingface/`, which is bind-mounted and reused.

Requires an NVIDIA driver new enough for CUDA 12.4, plus GPU access in Docker (Docker Desktop WSL integration, or the NVIDIA Container Toolkit). An RTX 3060 12 GB is enough for the default 832×1216 render.

```bash
docker compose build
# smoke test (imports only; does not load the model)
docker run --rm --gpus all --user "$(id -u):$(id -g)" --entrypoint python anime-diffusion-mcp:latest \
  -c "import torch; assert torch.version.cuda and torch.cuda.is_available(); print(torch.version.cuda)"
```

Point the MCP client at the absolute path of `scripts/mcp-docker.sh` (see `.mcp.json.example`). The script runs `docker run -i --rm --gpus all` — stdin attached, **no TTY** — and bind-mounts `checkpoints/`, `loras/`, `outputs/` and `.cache/`. Do not add `-t`; a TTY corrupts the MCP protocol. `CUDA_VISIBLE_DEVICES` defaults to `0`.

A gated Hugging Face repo needs `HF_TOKEN` in the client env; the script forwards it. Custom checkpoints and LoRAs stay in `checkpoints/` and `loras/` on the host — drop files there, no rebuild.

## MCP client configuration

Add the server to your MCP client (Claude Desktop, Claude Code, Cursor, ...).

Docker (recommended, see `.mcp.json.example`) — use the **absolute** path, clients often ignore the project cwd:

```json
{
  "mcpServers": {
    "anime-diffusion": {
      "command": "/absolute/path/to/anime-diffusion-mcp/scripts/mcp-docker.sh",
      "env": { "CUDA_VISIBLE_DEVICES": "0" }
    }
  }
}
```

Without Docker, `command` is `anime-diffusion-mcp` (or the venv script, e.g. `.venv/bin/anime-diffusion-mcp`). The process uses the **current working directory** for `checkpoints/`, `loras/` and `outputs/`, so launch it from the project folder (or set `cwd`).

## Tools

| Tool | Purpose |
|---|---|
| `validate_prompt(prompt, width, height, negative_prompt)` | Check a prompt against Animagine XL rules: quality tags present and last, 8+ tags, character/series consistency, resolution risk. Returns `valid`, `issues`, `suggestions`. |
| `optimize_prompt(description \| prompt)` | Reorder tags into canonical order (subject → character → series → appearance → composition → environment → style → quality) and fill missing essentials. Returns `optimized_prompt`, `actions`, `warnings`. |
| `list_models()` | Discover checkpoints in `checkpoints/` and LoRAs in `loras/`. |
| `generate_image(prompt, ...)` | Generate an image. Pass `image_path` for img2img. Supports `checkpoint`, `loras` + `lora_scales`, `width`/`height`, `steps`, `guidance_scale`, `seed`, `render_type`. |

Typical agent flow: `optimize_prompt` → `validate_prompt` → `generate_image`.

### `generate_image` example

```json
{
  "prompt": "1girl, solo, hatsune miku, vocaloid, long hair, twintails, smile, upper body, city night, neon lights, masterpiece, best quality, very aesthetic, absurdres",
  "width": 832,
  "height": 1216,
  "steps": 28,
  "guidance_scale": 5.0,
  "seed": 42
}
```

Add `"image_path": "C:/path/to/source.png", "strength": 0.5` for image-to-image (output size follows the source).
Add `"loras": ["my_style.safetensors"], "lora_scales": [0.8]` to apply LoRAs — they are applied per call; a call without `loras` runs on the bare checkpoint.

Set `"render_type": "gpu"` to abort instead of silently falling back to a slow CPU render when CUDA isn't available.

## Models

- **Base model**: `cagliostrolab/animagine-xl-4.0`, fetched from HuggingFace (cached in `~/.cache/huggingface`).
- **Custom checkpoints**: drop SDXL `.safetensors` files into `checkpoints/` and reference them by filename.
- **LoRAs**: drop `.safetensors` files into `loras/`. Multiple LoRAs can be combined with independent scales.

## Outputs

Images are written to `outputs/YYYY-MM-DD/anime_HHMMSS.png` with a sidecar `.json` containing prompt, negative prompt, seed, size, steps, guidance, checkpoint, LoRAs and render type — enough to reproduce the image.

## Prompt rules (short version)

Animagine XL 4.0 expects Danbooru-style comma-separated tags:

1. End with quality tags: `masterpiece, best quality, very aesthetic, absurdres`.
2. Start with subject count (`1girl`, `1boy`, `2girls`, ...).
3. Character tags should be followed by their series tag.
4. Aim for 8+ tags; order: subject → character → series → appearance → composition → environment → style → quality.
5. Use the default negative prompt unless you have a reason not to.

`validate_prompt` and `optimize_prompt` enforce these for you.

## Development

```bash
pip install -e .
python -c "from anime_diffusion_mcp.server import mcp; print(mcp.name)"
```

Package layout:

```
src/anime_diffusion_mcp/
├── server.py        # FastMCP tools
├── prompt/          # tokenizer, classifier, validator, optimizer
├── diffusion/       # ImagePipeline (Diffusers wrapper, checkpoint/LoRA handling)
└── contracts/       # Pydantic schemas and error codes
```

## License

MIT — see [LICENSE](LICENSE).

Model by [Cagliostro Research Lab](https://huggingface.co/cagliostrolab). Built with [FastMCP](https://github.com/jlowin/fastmcp) and [Diffusers](https://github.com/huggingface/diffusers).
