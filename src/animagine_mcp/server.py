"""Animagine XL 4.0 MCP Server.

Exposes tools for prompt validation, optimization, explanation, and image generation
with checkpoint and LoRA support.
"""

from fastmcp import FastMCP

from .contracts import (
    ValidatePromptOutput,
    OptimizePromptOutput,
    ExplainPromptOutput,
    GenerateImageOutput,
    ListModelsOutput,
    LoadCheckpointOutput,
    UnloadLorasOutput,
)
from .prompt import (
    validate_prompt as _validate_prompt,
    optimize_prompt as _optimize_prompt,
    explain_prompt as _explain_prompt,
)
from .diffusion import DEFAULT_NEGATIVE_PROMPT
from .diffusion.pipeline import get_pipeline



mcp = FastMCP(
    "Animagine XL 4.0",
    instructions="MCP server for Animagine XL 4.0 image generation with prompt validation and optimization",
)


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
def explain_prompt(prompt: str) -> dict:
    """Explain what each tag in a prompt does.

    Breaks down the prompt into individual tags with:
    - Category classification (quality, composition, character, etc.)
    - Explanation of what each tag affects
    - Canonically ordered version of the prompt

    Args:
        prompt: The prompt to explain

    Returns:
        Tag-by-tag breakdown with explanations
    """
    result = _explain_prompt(prompt)
    return result.model_dump()





@mcp.tool
def list_models() -> dict:
    """List available checkpoints and LoRAs for image generation.

    Returns all available models with metadata:
    - checkpoints: Base models (Animagine XL)
    - loras: Style modifiers and speed optimizations

    Use this to discover what models are available before generation.

    Returns:
        Dictionary with checkpoints, loras, default_checkpoint, and currently_loaded
    """
    pipeline = get_pipeline()
    return pipeline.list_available_models()


@mcp.tool
def load_checkpoint(checkpoint: str | None = None) -> dict:
    """Pre-load a checkpoint into GPU memory.

    Loading a checkpoint in advance speeds up subsequent generation calls.
    Use list_models() to see available checkpoints.

    Args:
        checkpoint: Filename from checkpoints/ folder (e.g., "custom_checkpoint.safetensors").
                   Use 'default' or None for Animagine XL 4.0 from HuggingFace.

    Returns:
        Status with success, checkpoint_loaded, vram_estimate_gb, and message
    """
    pipeline = get_pipeline()
    return pipeline.load_checkpoint(checkpoint)


@mcp.tool
def unload_loras() -> dict:
    """Unload all LoRA weights from the current pipeline.

    Useful to reset to base checkpoint style without reloading the full model.
    This is faster than reloading the checkpoint.

    Returns:
        Status with success, unloaded_count, and message
    """
    pipeline = get_pipeline()
    return pipeline.unload_loras()





@mcp.tool
def generate_image(
    prompt: str,
    negative_prompt: str | None = None,
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
    """Generate an image with Animagine XL 4.0.

    Uses the Diffusers pipeline with the lpw_stable_diffusion_xl custom pipeline.
    Images are saved to outputs/YYYY-MM-DD/ with accompanying metadata JSON.

    Supports custom checkpoints and LoRA mixing for style control.

    Recommended workflow:
    1. list_models → see available checkpoints and LoRAs
    2. validate_prompt → check for issues
    3. optimize_prompt → improve structure
    4. generate_image → create the image

    Args:
        prompt: The positive prompt (pre-validated recommended)
        negative_prompt: Optional; defaults to standard negative prompt
        checkpoint: Checkpoint filename or 'default' for HuggingFace model.
                   Examples: "custom_checkpoint.safetensors" (user's local checkpoint)
        loras: List of LoRA filenames to apply (in order).
               Examples: ["custom_lora.safetensors"] (user's local LoRAs)
        lora_scales: Scale/strength per LoRA (0.0-2.0, defaults to 1.0 for each).
                    Example: [0.8, 0.5] for two LoRAs
        width: Image width (default 832, portrait)
        height: Image height (default 1216, portrait)
        steps: Inference steps (default 28, use 4-8 with LCM LoRA)
        guidance_scale: CFG scale (default 5.0, use 1.5 with LCM LoRA)
        seed: Random seed for reproducibility (random if not set)
        render_type: Optional render type specification ('gpu' or 'cpu'). If specified and doesn't match detected device, renders are aborted to prevent slow processing.

    Returns:
        Image path, final prompts used, and generation metadata including
        checkpoint and LoRA information
    """
    pipeline = get_pipeline()


    lora_configs = None
    if loras:
        scales = lora_scales or [1.0] * len(loras)
        lora_configs = [
            {"filename": lora, "scale": scale}
            for lora, scale in zip(loras, scales)
        ]

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


@mcp.tool
def generate_image_from_image(
    image_path: str,
    prompt: str,
    negative_prompt: str | None = None,
    strength: float = 0.75,
    checkpoint: str | None = None,
    loras: list[str] | None = None,
    lora_scales: list[float] | None = None,
    steps: int = 28,
    guidance_scale: float = 5.0,
    seed: int | None = None,
    render_type: str | None = None,
) -> dict:
    """Generate an image using img2img (image-to-image) transformation.

    Takes an existing image and transforms it based on the prompt while
    preserving structure according to the strength parameter.

    Use cases:
    - Style transfer (apply anime/comic/realistic style to photo)
    - Image refinement (improve details, fix artifacts)
    - Pose/composition preservation (keep layout, change style)
    - Character consistency (transform existing character art)

    Args:
        image_path: Absolute path to source image to transform
        prompt: The positive prompt describing desired output
        negative_prompt: Optional; defaults to standard negative prompt
        strength: Denoising strength (0.0-1.0). Controls how much to change.
                 - 0.0-0.3: Minor refinements, preserve most details
                 - 0.3-0.5: Moderate changes, good for style transfer
                 - 0.5-0.7: Significant changes, keeps composition
                 - 0.7-1.0: Major transformation, only basic structure preserved
        checkpoint: Checkpoint filename or 'default' for HuggingFace model
        loras: List of LoRA filenames to apply (in order)
        lora_scales: Scale/strength per LoRA (0.0-2.0, defaults to 1.0)
        steps: Inference steps (default 28, use 4-8 with LCM LoRA)
        guidance_scale: CFG scale (default 5.0)
        seed: Random seed for reproducibility (random if not set)
        render_type: Optional render type specification ('gpu' or 'cpu'). If specified and doesn't match detected device, renders are aborted to prevent slow processing.

    Returns:
        Image path, final prompts used, and generation metadata including
        source image path and strength used
    """
    pipeline = get_pipeline()


    lora_configs = None
    if loras:
        scales = lora_scales or [1.0] * len(loras)
        lora_configs = [
            {"filename": lora, "scale": scale}
            for lora, scale in zip(loras, scales)
        ]

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
    return result.model_dump()


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
