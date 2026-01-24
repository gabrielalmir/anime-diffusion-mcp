"""Pydantic schemas for MCP tool inputs and outputs."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Severity(StrEnum):
    """Issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Issue(BaseModel):
    """Validation issue structure."""

    code: str = Field(description="Error code identifier")
    severity: Severity = Field(description="Issue severity")
    message: str = Field(description="Short, clear message")
    hint: str | None = Field(default=None, description="How to fix in one sentence")


class ValidatePromptOutput(BaseModel):
    """Output from validate_prompt tool."""

    valid: bool = Field(description="Whether the prompt passes validation")
    issues: list[Issue] = Field(default_factory=list, description="List of issues found")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")


class OptimizePromptOutput(BaseModel):
    """Output from optimize_prompt tool."""

    optimized_prompt: str = Field(description="The optimized prompt")
    actions: list[str] = Field(default_factory=list, description="Actions taken")
    warnings: list[str] = Field(default_factory=list, description="Warnings about the optimization")


class TagExplanation(BaseModel):
    """Explanation of a single tag."""

    tag: str = Field(description="The tag")
    category: str = Field(description="Tag category")
    explanation: str = Field(description="What this tag does")


class ExplainPromptOutput(BaseModel):
    """Output from explain_prompt tool."""

    breakdown: list[TagExplanation] = Field(description="Tag-by-tag breakdown")
    ordered_prompt: str | None = Field(default=None, description="Prompt reordered canonically")


class LoRAConfig(BaseModel):
    """Configuration for a single LoRA."""

    filename: str = Field(description="LoRA filename")
    scale: float = Field(default=1.0, ge=0.0, le=2.0, description="LoRA strength")


class ImageMetadata(BaseModel):
    """Metadata for a generated image."""

    prompt: str
    negative_prompt: str
    seed: int
    width: int
    height: int
    steps: int
    guidance_scale: float
    model_id: str = "cagliostrolab/animagine-xl-4.0"
    pipeline: str = "lpw_stable_diffusion_xl"
    checkpoint: str = Field(default="default", description="Checkpoint used")
    loras: list[LoRAConfig] = Field(default_factory=list, description="LoRAs applied")
                    
    source_image: str | None = Field(default=None, description="Source image path for img2img")
    strength: float | None = Field(default=None, description="Denoising strength for img2img (0.0-1.0)")


class GenerateImageOutput(BaseModel):
    """Output from generate_image tool."""

    image_path: str = Field(description="Path to the generated image")
    final_prompt: str = Field(description="The prompt actually used")
    final_negative_prompt: str = Field(description="The negative prompt actually used")
    metadata: ImageMetadata = Field(description="Generation metadata")


class ModelInfo(BaseModel):
    """Information about a checkpoint or LoRA."""

    name: str = Field(description="Human-readable name")
    filename: str = Field(description="File to reference in generate calls")
    size_mb: float = Field(description="Size in megabytes")
    description: str = Field(description="Brief description")


class ListModelsOutput(BaseModel):
    """Output for list_models tool."""

    checkpoints: list[ModelInfo] = Field(description="Available checkpoints")
    loras: list[ModelInfo] = Field(description="Available LoRAs")
    default_checkpoint: str = Field(description="Default checkpoint name")
    currently_loaded: str | None = Field(description="Currently loaded checkpoint")


class LoadCheckpointOutput(BaseModel):
    """Output for load_checkpoint tool."""

    success: bool
    checkpoint_loaded: str | None
    vram_estimate_gb: float
    message: str


class UnloadLorasOutput(BaseModel):
    """Output for unload_loras tool."""

    success: bool
    unloaded_count: int
    message: str
