"""anime-diffusion-mcp server.

Exposes tools for prompt validation, optimization and anime image generation
(Animagine XL 4.0) with checkpoint and LoRA support.
"""

from fastmcp import FastMCP

from .prompt import (
    validate_prompt as _validate_prompt,
    optimize_prompt as _optimize_prompt,
)
from .diffusion import get_pipeline


mcp = FastMCP(
    "anime-diffusion",
    instructions="Anime image generation (Animagine XL 4.0) with prompt validation and optimization",
)


def _build_lora_configs(
    loras: list[str] | None,
    lora_scales: list[float] | None,
) -> list[dict] | None:
    """Pair LoRA filenames with their scales, defaulting to 1.0."""
    if not loras:
        return None
    scales = lora_scales or [1.0] * len(loras)
    if len(scales) != len(loras):
        raise ValueError(
            f"lora_scales length ({len(scales)}) must match loras length ({len(loras)})"
        )
    return [{"filename": lora, "scale": scale} for lora, scale in zip(loras, scales)]


@mcp.tool
def validate_prompt(
    prompt: str,
    width: int = 832,
    height: int = 1216,
    negative_prompt: str | None = None,
) -> dict:
    """Validate a prompt against Animagine XL rules.

    Checks for:
    - Required quality tags (masterpiece, best quality, etc.)
    - Proper tag ordering (quality tags at end)
    - Minimum tag count (8+ recommended)
    - Character/series consistency
    - Resolution compatibility

    Args:
        prompt: The prompt to validate
        width: Target image width (default 832)
        height: Target image height (default 1216)
        negative_prompt: Optional negative prompt to check

    Returns:
        Validation result with issues and suggestions
    """
    result = _validate_prompt(
        prompt=prompt,
        width=width,
        height=height,
        negative_prompt=negative_prompt,
    )
    return result.model_dump()


@mcp.tool
def optimize_prompt(
    description: str | None = None,
    prompt: str | None = None,
) -> dict:
    """Optimize a prompt for Animagine XL.

    Provide either a natural language description or an existing prompt.
    The optimizer will:
    - Reorder tags by canonical category order
    - Move quality tags to the end
    - Add missing essential categories (composition, environment, quality)

    Args:
        description: Natural language description to convert to tags
        prompt: Existing tag-based prompt to optimize

    Returns:
        Optimized prompt with list of actions taken
    """
    result = _optimize_prompt(description=description, prompt=prompt)
    return result.model_dump()


@mcp.tool
def list_models() -> dict:
    """List available checkpoints and LoRAs for image generation.

    Checkpoints are discovered from the checkpoints/ folder and LoRAs from
    the loras/ folder (.safetensors files). The default checkpoint is
    Animagine XL 4.0 from HuggingFace.

    Returns:
        Dictionary with checkpoints, loras, default_checkpoint, and currently_loaded
    """
    return get_pipeline().list_available_models()


@mcp.tool
def generate_image(
    prompt: str,
    negative_prompt: str | None = None,
    image_path: str | None = None,
    strength: float = 0.75,
    checkpoint: str | None = None,
    loras: list[str] | None = None,
    lora_scales: list[float] | None = None,
    width: int = 832,
    height: int = 1216,
    steps: int = 28,
    guidance_scale: float = 5.0,
    seed: int | None = None,
    render_type: str | None = None,
) -> dict:
    """Generate an anime image (text-to-image or image-to-image).

    Images are saved to outputs/YYYY-MM-DD/ with a sidecar metadata JSON.
    The checkpoint is loaded on demand; LoRAs are applied per call (a call
    without `loras` runs on the bare checkpoint).

    Recommended workflow:
    1. list_models → see available checkpoints and LoRAs
    2. validate_prompt / optimize_prompt → improve the prompt
    3. generate_image → create the image

    Args:
        prompt: The positive prompt (pre-validated recommended)
        negative_prompt: Optional; defaults to the standard negative prompt
        image_path: Optional source image. When given, runs img2img and
                    `width`/`height` are ignored (output follows the source).
        strength: img2img denoising strength (0.0-1.0). 0.3-0.5 style
                  transfer, 0.7+ major transformation. Ignored for txt2img.
        checkpoint: Checkpoint filename from checkpoints/ or 'default' for HuggingFace model
        loras: List of LoRA filenames from loras/ to apply (in order)
        lora_scales: Scale per LoRA (0.0-2.0, defaults to 1.0 for each)
        width: Image width (default 832, portrait)
        height: Image height (default 1216, portrait)
        steps: Inference steps (default 28, use 4-8 with LCM LoRA)
        guidance_scale: CFG scale (default 5.0, use 1.5 with LCM LoRA)
        seed: Random seed for reproducibility (random if not set)
        render_type: Optional 'gpu' or 'cpu'. If it doesn't match the detected
                     device the render is aborted to prevent slow processing.

    Returns:
        Image path, final prompts used, and generation metadata
    """
    pipeline = get_pipeline()
    lora_configs = _build_lora_configs(loras, lora_scales)

    if image_path:
        result = pipeline.generate_img2img(
            image_path=image_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            strength=strength,
            checkpoint=checkpoint,
            loras=lora_configs,
            steps=steps,
            guidance_scale=guidance_scale,
            seed=seed,
            render_type=render_type,
        )
    else:
        result = pipeline.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            checkpoint=checkpoint,
            loras=lora_configs,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=guidance_scale,
            seed=seed,
            render_type=render_type,
        )
    return result.model_dump()


def main():
    """Run the MCP server (stdio)."""
    mcp.run()


if __name__ == "__main__":
    main()
