"""FastAPI REST API server for Animagine XL 4.0.

Provides HTTP endpoints for prompt validation, optimization, explanation,
and image generation with checkpoint and LoRA support.
"""

import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Animagine XL 4.0 API",
    description="REST API for Animagine XL 4.0 image generation with prompt validation and optimization",
    version="0.1.0",
)


# ============================================================================
# Pydantic Request Models
# ============================================================================


class ValidatePromptRequest(BaseModel):
    """Request model for prompt validation."""

    prompt: str = Field(..., description="The prompt to validate")
    width: int = Field(832, description="Target image width")
    height: int = Field(1216, description="Target image height")
    negative_prompt: Optional[str] = Field(None, description="Optional negative prompt to check")


class OptimizePromptRequest(BaseModel):
    """Request model for prompt optimization."""

    description: Optional[str] = Field(None, description="Natural language description to convert to tags")
    prompt: Optional[str] = Field(None, description="Existing tag-based prompt to optimize")


class ExplainPromptRequest(BaseModel):
    """Request model for prompt explanation."""

    prompt: str = Field(..., description="The prompt to explain")


class GenerateImageRequest(BaseModel):
    """Request model for image generation."""

    prompt: str = Field(..., description="The positive prompt (pre-validated recommended)")
    negative_prompt: Optional[str] = Field(None, description="Optional negative prompt")
    checkpoint: Optional[str] = Field(None, description="Checkpoint filename or 'default'")
    loras: Optional[list[str]] = Field(None, description="List of LoRA filenames to apply")
    lora_scales: Optional[list[float]] = Field(None, description="Scale/strength per LoRA")
    width: int = Field(832, description="Image width")
    height: int = Field(1216, description="Image height")
    steps: int = Field(28, description="Inference steps")
    guidance_scale: float = Field(5.0, description="CFG scale")
    seed: Optional[int] = Field(None, description="Random seed")


class GenerateImageFromImageRequest(BaseModel):
    """Request model for img2img generation."""

    image_path: str = Field(..., description="Absolute path to source image")
    prompt: str = Field(..., description="The positive prompt")
    negative_prompt: Optional[str] = Field(None, description="Optional negative prompt")
    strength: float = Field(0.75, description="Denoising strength (0.0-1.0)")
    checkpoint: Optional[str] = Field(None, description="Checkpoint filename")
    loras: Optional[list[str]] = Field(None, description="List of LoRA filenames")
    lora_scales: Optional[list[float]] = Field(None, description="Scale/strength per LoRA")
    steps: int = Field(28, description="Inference steps")
    guidance_scale: float = Field(5.0, description="CFG scale")
    seed: Optional[int] = Field(None, description="Random seed")


class LoadCheckpointRequest(BaseModel):
    """Request model for loading checkpoint."""

    checkpoint: Optional[str] = Field(None, description="Checkpoint filename or 'default'")


# ============================================================================
# Endpoints - Prompt Operations
# ============================================================================


@app.post("/api/v1/validate-prompt", response_model=ValidatePromptOutput)
async def validate_prompt(request: ValidatePromptRequest) -> ValidatePromptOutput:
    """Validate a prompt against Animagine XL rules.

    Checks for:
    - Required quality tags (masterpiece, best quality, etc.)
    - Proper tag ordering (quality tags at end)
    - Minimum tag count (8+ recommended)
    - Character/series consistency
    - Resolution compatibility
    """
    try:
        result = _validate_prompt(
            prompt=request.prompt,
            width=request.width,
            height=request.height,
            negative_prompt=request.negative_prompt,
        )
        return result
    except Exception as e:
        logger.error(f"Prompt validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@app.post("/api/v1/optimize-prompt", response_model=OptimizePromptOutput)
async def optimize_prompt(request: OptimizePromptRequest) -> OptimizePromptOutput:
    """Optimize a prompt for Animagine XL.

    Provide either a natural language description or an existing prompt.
    The optimizer will:
    - Reorder tags by canonical category order
    - Move quality tags to the end
    - Add missing essential categories (composition, environment, quality)
    """
    try:
        if not request.description and not request.prompt:
            raise ValueError("Either 'description' or 'prompt' must be provided")

        result = _optimize_prompt(
            description=request.description,
            prompt=request.prompt,
        )
        return result
    except Exception as e:
        logger.error(f"Prompt optimization error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Optimization failed: {str(e)}")


@app.post("/api/v1/explain-prompt", response_model=ExplainPromptOutput)
async def explain_prompt(request: ExplainPromptRequest) -> ExplainPromptOutput:
    """Explain what each tag in a prompt does.

    Breaks down the prompt into individual tags with:
    - Category classification
    - Explanation of what each tag affects
    - Canonically ordered version of the prompt
    """
    try:
        result = _explain_prompt(request.prompt)
        return result
    except Exception as e:
        logger.error(f"Prompt explanation error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Explanation failed: {str(e)}")


# ============================================================================
# Endpoints - Model Operations
# ============================================================================


@app.get("/api/v1/models", response_model=ListModelsOutput)
async def list_models() -> ListModelsOutput:
    """List available checkpoints and LoRAs for image generation.

    Returns all available models with metadata:
    - checkpoints: Base models (Animagine XL)
    - loras: Style modifiers and speed optimizations
    """
    try:
        pipeline = get_pipeline()
        result = pipeline.list_available_models()
        return ListModelsOutput(**result)
    except Exception as e:
        logger.error(f"List models error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@app.post("/api/v1/load-checkpoint", response_model=LoadCheckpointOutput)
async def load_checkpoint(request: LoadCheckpointRequest) -> LoadCheckpointOutput:
    """Pre-load a checkpoint into GPU memory.

    Loading a checkpoint in advance speeds up subsequent generation calls.
    Use GET /api/v1/models to see available checkpoints.
    """
    try:
        pipeline = get_pipeline()
        result = pipeline.load_checkpoint(request.checkpoint)
        return LoadCheckpointOutput(**result)
    except Exception as e:
        logger.error(f"Load checkpoint error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to load checkpoint: {str(e)}")


@app.post("/api/v1/unload-loras", response_model=UnloadLorasOutput)
async def unload_loras() -> UnloadLorasOutput:
    """Unload all LoRA weights from the current pipeline.

    Useful to reset to base checkpoint style without reloading the full model.
    """
    try:
        pipeline = get_pipeline()
        result = pipeline.unload_loras()
        return UnloadLorasOutput(**result)
    except Exception as e:
        logger.error(f"Unload LoRAs error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to unload LoRAs: {str(e)}")


# ============================================================================
# Endpoints - Image Generation
# ============================================================================


@app.post("/api/v1/generate", response_model=GenerateImageOutput)
async def generate_image(request: GenerateImageRequest) -> GenerateImageOutput:
    """Generate an image with Animagine XL 4.0.

    Uses the Diffusers pipeline with custom optimizations.
    Images are saved to outputs/YYYY-MM-DD/ with accompanying metadata JSON.

    Recommended workflow:
    1. GET /api/v1/models → see available checkpoints and LoRAs
    2. POST /api/v1/validate-prompt → check for issues
    3. POST /api/v1/optimize-prompt → improve structure
    4. POST /api/v1/generate → create the image
    """
    try:
        pipeline = get_pipeline()

        lora_configs = None
        if request.loras:
            scales = request.lora_scales or [1.0] * len(request.loras)
            lora_configs = [
                {"filename": lora, "scale": scale}
                for lora, scale in zip(request.loras, scales)
            ]

        result = pipeline.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            checkpoint=request.checkpoint,
            loras=lora_configs,
            width=request.width,
            height=request.height,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
        )
        return GenerateImageOutput(**result)
    except Exception as e:
        logger.error(f"Image generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/api/v1/generate-img2img", response_model=GenerateImageOutput)
async def generate_image_from_image(request: GenerateImageFromImageRequest) -> GenerateImageOutput:
    """Generate an image using img2img (image-to-image) transformation.

    Takes an existing image and transforms it based on the prompt while
    preserving structure according to the strength parameter.

    Use cases:
    - Style transfer (apply anime/comic/realistic style to photo)
    - Image refinement (improve details, fix artifacts)
    - Pose/composition preservation (keep layout, change style)
    - Character consistency (transform existing character art)
    """
    try:
        pipeline = get_pipeline()

        lora_configs = None
        if request.loras:
            scales = request.lora_scales or [1.0] * len(request.loras)
            lora_configs = [
                {"filename": lora, "scale": scale}
                for lora, scale in zip(request.loras, scales)
            ]

        result = pipeline.generate_img2img(
            image_path=request.image_path,
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            strength=request.strength,
            checkpoint=request.checkpoint,
            loras=lora_configs,
            steps=request.steps,
            guidance_scale=request.guidance_scale,
            seed=request.seed,
        )
        return GenerateImageOutput(**result)
    except Exception as e:
        logger.error(f"Img2img generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


# ============================================================================
# Utility Endpoints
# ============================================================================


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    try:
        pipeline = get_pipeline()
        result = pipeline.list_available_models()
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "checkpoints_available": len(result.get("checkpoints", [])),
                "loras_available": len(result.get("loras", [])),
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
            },
        )


@app.get("/api/v1/status")
async def status() -> JSONResponse:
    """Get current system status."""
    try:
        pipeline = get_pipeline()
        models = pipeline.list_available_models()
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "checkpoint_loaded": models.get("currently_loaded"),
                "default_checkpoint": models.get("default_checkpoint"),
                "checkpoints_available": len(models.get("checkpoints", [])),
                "loras_available": len(models.get("loras", [])),
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "error": str(e),
            },
        )


# ============================================================================
# Root Endpoint
# ============================================================================


@app.get("/")
async def root() -> JSONResponse:
    """API root endpoint with documentation links."""
    return JSONResponse(
        content={
            "name": "Animagine XL 4.0 API",
            "version": "0.1.0",
            "documentation": "/docs",
            "endpoints": {
                "prompt_validation": {
                    "validate": "POST /api/v1/validate-prompt",
                    "optimize": "POST /api/v1/optimize-prompt",
                    "explain": "POST /api/v1/explain-prompt",
                },
                "models": {
                    "list": "GET /api/v1/models",
                    "load_checkpoint": "POST /api/v1/load-checkpoint",
                    "unload_loras": "POST /api/v1/unload-loras",
                },
                "generation": {
                    "generate": "POST /api/v1/generate",
                    "generate_img2img": "POST /api/v1/generate-img2img",
                },
                "utility": {
                    "health": "GET /health",
                    "status": "GET /api/v1/status",
                },
            },
        }
    )


def main():
    """Run the API server."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
