"""Diffusers pipeline wrapper for Animagine XL 4.0 with checkpoint and LoRA support."""

import json
import logging
import random
from datetime import datetime
from pathlib import Path

import torch
from PIL import Image

from ..contracts import GenerateImageOutput, ImageMetadata, LoRAConfig

logger = logging.getLogger(__name__)


MODEL_ID = "cagliostrolab/animagine-xl-4.0"
CUSTOM_PIPELINE = "lpw_stable_diffusion_xl"


DEFAULT_WIDTH = 832
DEFAULT_HEIGHT = 1216
DEFAULT_STEPS = 28
DEFAULT_GUIDANCE = 5.0


DEFAULT_NEGATIVE_PROMPT = (
    "lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, "
    "fewer digits, cropped, worst quality, low quality, low score, bad score, "
    "average score, signature, watermark, username, blurry"
)


CHECKPOINTS_DIR = Path("checkpoints")
LORAS_DIR = Path("loras")


def _discover_checkpoints() -> dict:
    """Dynamically discover available checkpoints in checkpoints/ folder."""
    registry = {
        "default": {
            "name": "Animagine XL 4.0 (HuggingFace)",
            "path": None,
            "description": "Default anime model from HuggingFace",
        },
    }

    if CHECKPOINTS_DIR.exists():
        for file in CHECKPOINTS_DIR.glob("*.safetensors"):
            if file.name not in registry:
                registry[file.name] = {
                    "name": file.stem,
                    "path": str(file),
                    "description": f"Custom checkpoint: {file.name}",
                }

    return registry


def _discover_loras() -> dict:
    """Dynamically discover available LoRAs in loras/ folder."""
    registry = {}

    if LORAS_DIR.exists():
        for file in LORAS_DIR.glob("*.safetensors"):
            registry[file.name] = {
                "name": file.stem,
                "path": str(file),
                "description": f"LoRA: {file.name}",
            }

    return registry


class ImagePipeline:
    """Wrapper for the Animagine XL 4.0 Diffusers pipeline with checkpoint/LoRA support."""

    def __init__(self, output_dir: str | Path = "outputs"):
        self._pipe = None
        self._device = None
        self.output_dir = Path(output_dir)
        self._loaded_checkpoint: str | None = None
        self._loaded_loras: list[LoRAConfig] = []

    # ------------------------------------------------------------------ device

    def _get_detected_render_type(self) -> str:
        """Detect the current render type (gpu or cpu)."""
        return "gpu" if torch.cuda.is_available() else "cpu"

    def _validate_render_type(self, specified_render_type: str | None) -> tuple[bool, str]:
        """Validate that specified render type matches detected render type.

        Returns:
            Tuple of (is_valid, detected_render_type)
        """
        detected = self._get_detected_render_type()
        if specified_render_type is None:
            return True, detected

        specified = specified_render_type.lower()
        if specified not in ("gpu", "cpu") or specified != detected:
            return False, detected

        return True, detected

    @property
    def device(self) -> str:
        """Get the device to use for generation."""
        if self._device is None:
            self._device = "cuda" if torch.cuda.is_available() else "cpu"
        return self._device

    @property
    def is_cuda_available(self) -> bool:
        """Check if CUDA is available."""
        return torch.cuda.is_available()

    @property
    def loaded_checkpoint(self) -> str | None:
        """Get the currently loaded checkpoint name."""
        return self._loaded_checkpoint

    @property
    def loaded_loras(self) -> list[LoRAConfig]:
        """Get the currently loaded LoRAs."""
        return self._loaded_loras.copy()

    # ------------------------------------------------------------------ models

    def list_available_models(self) -> dict:
        """List all available checkpoints and LoRAs with metadata."""
        checkpoints = []
        for filename, info in _discover_checkpoints().items():
            if info["path"] is None:
                size_mb = 0
            else:
                path = Path(info["path"])
                if not path.exists():
                    continue
                size_mb = round(path.stat().st_size / (1024 * 1024), 1)
            checkpoints.append({
                "name": info["name"],
                "filename": filename,
                "size_mb": size_mb,
                "description": info["description"],
            })

        loras = []
        for filename, info in _discover_loras().items():
            path = LORAS_DIR / filename
            if path.exists():
                loras.append({
                    "name": info["name"],
                    "filename": filename,
                    "size_mb": round(path.stat().st_size / (1024 * 1024), 1),
                    "description": info["description"],
                })

        return {
            "checkpoints": checkpoints,
            "loras": loras,
            "default_checkpoint": "default",
            "currently_loaded": self._loaded_checkpoint,
        }

    def _load_from_huggingface(self):
        """Load default model from HuggingFace."""
        from diffusers import DiffusionPipeline

        self._pipe = DiffusionPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16 if self.is_cuda_available else torch.float32,
            use_safetensors=True,
            custom_pipeline=CUSTOM_PIPELINE,
        )
        self._pipe.to(self.device)
        if hasattr(self._pipe, "watermark"):
            self._pipe.watermark = None

    def _load_from_file(self, checkpoint: str):
        """Load checkpoint from local safetensors file."""
        from diffusers import StableDiffusionXLPipeline

        info = _discover_checkpoints().get(checkpoint)
        if not info or not info.get("path"):
            raise FileNotFoundError(f"Checkpoint not in registry: {checkpoint}")

        checkpoint_path = Path(info["path"])
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

        self._pipe = StableDiffusionXLPipeline.from_single_file(
            str(checkpoint_path),
            torch_dtype=torch.float16 if self.is_cuda_available else torch.float32,
            use_safetensors=True,
        )
        self._pipe.to(self.device)

    def _unload_pipeline(self):
        """Free GPU memory."""
        if self._pipe is not None:
            del self._pipe
            self._pipe = None
            self._loaded_checkpoint = None
            self._loaded_loras = []
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    def load_checkpoint(self, checkpoint: str | None = None) -> dict:
        """Load a specific checkpoint into memory.

        Args:
            checkpoint: Filename from checkpoints/ folder, or 'default' for HuggingFace model

        Returns:
            Status dict with success, loaded checkpoint name and message
        """
        checkpoint = checkpoint or "default"

        if self._loaded_checkpoint == checkpoint and self._pipe is not None:
            return {"success": True, "checkpoint_loaded": checkpoint, "message": "Checkpoint already loaded"}

        if self._pipe is not None:
            self._unload_pipeline()

        try:
            if checkpoint == "default":
                self._load_from_huggingface()
            else:
                self._load_from_file(checkpoint)
        except Exception as e:
            return {"success": False, "checkpoint_loaded": None, "message": f"Failed to load checkpoint: {e}"}

        self._loaded_checkpoint = checkpoint
        self._loaded_loras = []
        return {"success": True, "checkpoint_loaded": checkpoint, "message": f"Successfully loaded {checkpoint}"}

    # ------------------------------------------------------------------- LoRAs

    def _apply_loras(self, loras: list[dict] | None):
        """Replace the active LoRA set with `loras` (each {"filename", "scale"}).

        An empty/None list leaves the bare checkpoint active. Each LoRA is
        loaded as a named adapter and all scales are applied together via
        set_adapters, so every entry's scale takes effect.
        """
        self.unload_loras()
        if not loras:
            return

        lora_registry = _discover_loras()
        names, scales = [], []
        for i, cfg in enumerate(loras):
            filename = cfg["filename"]
            if filename not in lora_registry:
                raise FileNotFoundError(f"LoRA not found: {filename}")
            adapter_name = f"lora_{i}"
            self._pipe.load_lora_weights(str(LORAS_DIR), weight_name=filename, adapter_name=adapter_name)
            names.append(adapter_name)
            scales.append(cfg.get("scale", 1.0))
            self._loaded_loras.append(LoRAConfig(filename=filename, scale=scales[-1]))

        self._pipe.set_adapters(names, adapter_weights=scales)

    def unload_loras(self) -> int:
        """Unload all LoRAs from the pipeline. Returns the number unloaded."""
        count = len(self._loaded_loras)
        if self._pipe is not None and count > 0:
            try:
                self._pipe.unload_lora_weights()
            except Exception as e:
                logger.warning("Error unloading LoRAs: %s", e)
        self._loaded_loras = []
        return count

    # -------------------------------------------------------------- generation

    def _prepare(
        self,
        checkpoint: str | None,
        loras: list[dict] | None,
        render_type: str | None,
        seed: int | None,
    ) -> tuple[torch.Generator, int, str]:
        """Shared setup for txt2img/img2img: render type, checkpoint, LoRAs, seed."""
        is_valid, detected_render_type = self._validate_render_type(render_type)
        if not is_valid:
            raise ValueError(
                f"Render type mismatch: specified '{render_type}' but detected '{detected_render_type}'. "
                f"Aborting render to prevent slow processing. Ensure the required hardware "
                f"is available or remove the render_type parameter."
            )

        target_checkpoint = checkpoint or self._loaded_checkpoint or "default"
        if self._loaded_checkpoint != target_checkpoint or self._pipe is None:
            result = self.load_checkpoint(target_checkpoint)
            if not result["success"]:
                raise RuntimeError(result["message"])

        self._apply_loras(loras)

        if seed is None:
            seed = random.randint(0, 2**32 - 1)
        generator = torch.Generator(device=self.device).manual_seed(seed)
        return generator, seed, detected_render_type

    def _get_output_path(self) -> tuple[Path, Path]:
        """Get output paths for image and metadata."""
        date_dir = self.output_dir / datetime.now().strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)
        base_name = f"anime_{datetime.now().strftime('%H%M%S')}"

        counter = 0
        while True:
            suffix = f"_{counter}" if counter > 0 else ""
            image_path = date_dir / f"{base_name}{suffix}.png"
            meta_path = date_dir / f"{base_name}{suffix}.json"
            if not image_path.exists():
                return image_path, meta_path
            counter += 1

    def _save(self, image: Image.Image, metadata: ImageMetadata) -> GenerateImageOutput:
        """Save image + sidecar metadata JSON and build the output."""
        image_path, meta_path = self._get_output_path()
        image.save(image_path)
        with open(meta_path, "w") as f:
            json.dump(metadata.model_dump(), f, indent=2)

        return GenerateImageOutput(
            image_path=str(image_path.absolute()),
            final_prompt=metadata.prompt,
            final_negative_prompt=metadata.negative_prompt,
            metadata=metadata,
        )

    def generate(
        self,
        prompt: str,
        negative_prompt: str | None = None,
        checkpoint: str | None = None,
        loras: list[dict] | None = None,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        steps: int = DEFAULT_STEPS,
        guidance_scale: float = DEFAULT_GUIDANCE,
        seed: int | None = None,
        render_type: str | None = None,
    ) -> GenerateImageOutput:
        """Generate an image from text.

        Args:
            prompt: The positive prompt (should be pre-validated/optimized)
            negative_prompt: Optional negative prompt (default applied if None)
            checkpoint: Checkpoint filename or 'default' (None uses current/default)
            loras: List of LoRA configs [{"filename": "...", "scale": 1.0}]
            width: Image width (default 832)
            height: Image height (default 1216)
            steps: Inference steps (default 28, use 4-8 with LCM)
            guidance_scale: Classifier-free guidance scale (default 5.0)
            seed: Random seed for reproducibility (random if None)
            render_type: Optional 'gpu' or 'cpu'; mismatch with detected device raises ValueError

        Returns:
            GenerateImageOutput with image path and metadata
        """
        generator, seed, detected_render_type = self._prepare(checkpoint, loras, render_type, seed)
        final_negative = negative_prompt or DEFAULT_NEGATIVE_PROMPT

        result = self._pipe(
            prompt=prompt,
            negative_prompt=final_negative,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )

        metadata = ImageMetadata(
            prompt=prompt,
            negative_prompt=final_negative,
            seed=seed,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=guidance_scale,
            model_id=MODEL_ID,
            pipeline=CUSTOM_PIPELINE,
            checkpoint=self._loaded_checkpoint or "default",
            loras=self.loaded_loras,
            render_type=detected_render_type,
        )
        return self._save(result.images[0], metadata)

    def _load_source_image(self, image_path: str) -> Image.Image:
        """Load source image for img2img as RGB."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Source image not found: {image_path}")

        image = Image.open(path)
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image

    def _get_img2img_pipeline(self):
        """Create an img2img pipeline sharing components with the loaded text2img pipeline."""
        from diffusers import StableDiffusionXLImg2ImgPipeline

        img2img_pipe = StableDiffusionXLImg2ImgPipeline(
            vae=self._pipe.vae,
            text_encoder=self._pipe.text_encoder,
            text_encoder_2=self._pipe.text_encoder_2,
            tokenizer=self._pipe.tokenizer,
            tokenizer_2=self._pipe.tokenizer_2,
            unet=self._pipe.unet,
            scheduler=self._pipe.scheduler,
        )
        img2img_pipe.to(self.device)
        return img2img_pipe

    def generate_img2img(
        self,
        image_path: str,
        prompt: str,
        negative_prompt: str | None = None,
        strength: float = 0.75,
        checkpoint: str | None = None,
        loras: list[dict] | None = None,
        steps: int = DEFAULT_STEPS,
        guidance_scale: float = DEFAULT_GUIDANCE,
        seed: int | None = None,
        render_type: str | None = None,
    ) -> GenerateImageOutput:
        """Transform an existing image guided by the prompt (img2img).

        Args:
            image_path: Path to source image to transform
            prompt: The positive prompt describing desired output
            negative_prompt: Optional negative prompt (default applied if None)
            strength: Denoising strength (0.0-1.0). Higher = more change from source.
            checkpoint: Checkpoint filename or 'default' (None uses current/default)
            loras: List of LoRA configs [{"filename": "...", "scale": 1.0}]
            steps: Inference steps (default 28, use 4-8 with LCM)
            guidance_scale: Classifier-free guidance scale (default 5.0)
            seed: Random seed for reproducibility (random if None)
            render_type: Optional 'gpu' or 'cpu'; mismatch with detected device raises ValueError

        Returns:
            GenerateImageOutput with image path and metadata
        """
        source_image = self._load_source_image(image_path)
        generator, seed, detected_render_type = self._prepare(checkpoint, loras, render_type, seed)
        final_negative = negative_prompt or DEFAULT_NEGATIVE_PROMPT
        width, height = source_image.size

        result = self._get_img2img_pipeline()(
            prompt=prompt,
            negative_prompt=final_negative,
            image=source_image,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )

        metadata = ImageMetadata(
            prompt=prompt,
            negative_prompt=final_negative,
            seed=seed,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=guidance_scale,
            model_id=MODEL_ID,
            pipeline="img2img",
            checkpoint=self._loaded_checkpoint or "default",
            loras=self.loaded_loras,
            render_type=detected_render_type,
            source_image=str(Path(image_path).absolute()),
            strength=strength,
        )
        return self._save(result.images[0], metadata)


_pipeline: ImagePipeline | None = None


def get_pipeline(output_dir: str | Path = "outputs") -> ImagePipeline:
    """Get or create the global pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = ImagePipeline(output_dir=output_dir)
    return _pipeline
