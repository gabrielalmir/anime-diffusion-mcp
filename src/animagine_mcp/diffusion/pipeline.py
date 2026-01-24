"""Diffusers pipeline wrapper for Animagine XL 4.0 with checkpoint and LoRA support."""

import json
import random
from datetime import datetime
from pathlib import Path

import torch
from PIL import Image

from ..contracts import GenerateImageOutput, ImageMetadata, LoRAConfig
from ..contracts.errors import ErrorCode



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


def get_checkpoint_registry() -> dict:
    """Get current checkpoint registry (dynamically discovered)."""
    return _discover_checkpoints()


def get_lora_registry() -> dict:
    """Get current LoRA registry (dynamically discovered)."""
    return _discover_loras()


class AnimaginePipeline:
    """Wrapper for the Animagine XL 4.0 Diffusers pipeline with checkpoint/LoRA support."""

    def __init__(self, output_dir: str | Path = "outputs"):
        self._pipe = None
        self._device = None
        self.output_dir = Path(output_dir)
        self._loaded_checkpoint: str | None = None
        self._loaded_loras: list[LoRAConfig] = []

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
        """Get currently loaded checkpoint name."""
        return self._loaded_checkpoint

    @property
    def loaded_loras(self) -> list[LoRAConfig]:
        """Get list of currently loaded LoRAs."""
        return self._loaded_loras.copy()

    def list_available_models(self) -> dict:
        """Scan directories and return available models."""
        checkpoint_registry = get_checkpoint_registry()
        lora_registry = get_lora_registry()

        checkpoints = []
        for filename, info in checkpoint_registry.items():
            if filename == "default":
                checkpoints.append({
                    "name": info["name"],
                    "filename": filename,
                    "size_mb": 0,
                    "description": info["description"],
                })
            else:
                path = Path(info["path"])
                if path.exists():
                    size_mb = path.stat().st_size / (1024 * 1024)
                    checkpoints.append({
                        "name": info["name"],
                        "filename": filename,
                        "size_mb": round(size_mb, 1),
                        "description": info["description"],
                    })

        loras = []
        for filename, info in lora_registry.items():
            path = LORAS_DIR / filename
            if path.exists():
                size_mb = path.stat().st_size / (1024 * 1024)
                loras.append({
                    "name": info["name"],
                    "filename": filename,
                    "size_mb": round(size_mb, 1),
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

        checkpoint_registry = get_checkpoint_registry()
        info = checkpoint_registry.get(checkpoint)
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
            Status dict with success, loaded checkpoint name, VRAM estimate, and message
        """
        checkpoint = checkpoint or "default"


        if self._loaded_checkpoint == checkpoint and self._pipe is not None:
            return {
                "success": True,
                "checkpoint_loaded": checkpoint,
                "vram_estimate_gb": 6.5,
                "message": "Checkpoint already loaded",
            }


        if self._pipe is not None:
            self._unload_pipeline()

        try:
            if checkpoint == "default":
                self._load_from_huggingface()
            else:
                self._load_from_file(checkpoint)

            self._loaded_checkpoint = checkpoint
            self._loaded_loras = []

            return {
                "success": True,
                "checkpoint_loaded": checkpoint,
                "vram_estimate_gb": 6.5,
                "message": f"Successfully loaded {checkpoint}",
            }
        except FileNotFoundError as e:
            return {
                "success": False,
                "checkpoint_loaded": None,
                "vram_estimate_gb": 0,
                "message": str(e),
            }
        except Exception as e:
            return {
                "success": False,
                "checkpoint_loaded": None,
                "vram_estimate_gb": 0,
                "message": f"Failed to load checkpoint: {str(e)}",
            }

    def load_lora(self, filename: str, scale: float = 1.0) -> dict:
        """Load and apply a LoRA.

        Args:
            filename: LoRA filename from loras/ folder
            scale: LoRA strength (0.0-2.0, default 1.0)

        Returns:message
        """
        if self._pipe is None:
            return {
                "success": False,
                "lora_loaded": None,
                "scale": scale,
                "message": "No checkpoint loaded. Call load_checkpoint first.",
            }

        lora_path = LORAS_DIR / filename
        if not lora_path.exists():
            return {
                "success": False,
                "lora_loaded": None,
                "scale": scale,
                "message": f"LoRA not found: {filename}",
            }

        try:

            self._pipe.load_lora_weights(
                str(LORAS_DIR),
                weight_name=filename,
            )


            lora_config = LoRAConfig(filename=filename, scale=scale)
            self._loaded_loras.append(lora_config)


            if len(self._loaded_loras) == 1:
                self._pipe.fuse_lora(lora_scale=scale)

            return {
                "success": True,
                "lora_loaded": filename,
                "scale": scale,
                "message": f"Loaded {filename}",
            }
        except Exception as e:
            return {
                "success": False,
                "lora_loaded": None,
                "scale": scal,
                "is_lcm": False,
                "message": f"Failed to load LoRA: {str(e)}",
            }

    def unload_loras(self) -> dict:
        """Unload all LoRAs from the pipeline.

        Returns:
            Status dict with success, count of unloaded LoRAs, and message
        """
        if self._pipe is None:
            return {
                "success": True,
                "unloaded_count": 0,
                "message": "No pipeline loaded",
            }

        count = len(self._loaded_loras)
        if count > 0:
            try:
                self._pipe.unfuse_lora()
                self._pipe.unload_lora_weights()
            except Exception:
                pass
            self._loaded_loras = []

        return {
            "success": True,
            "unloaded_count": count,
            "message": f"Unloaded {count} LoRA(s)" if count > 0 else "No LoRAs to unload",
        }

    def _load_pipeline(self):
        """Lazy-load the Diffusers pipeline (legacy compatibility)."""
        if self._pipe is not None:
            return

        self._load_from_huggingface()
        self._loaded_checkpoint = "default"

    def _get_output_path(self) -> tuple[Path, Path]:
        """Get output paths for image and metadata."""
        date_dir = self.output_dir / datetime.now().strftime("%Y-%m-%d")
        date_dir.mkdir(parents=True, exist_ok=True)


        timestamp = datetime.now().strftime("%H%M%S")
        base_name = f"animagine_{timestamp}"


        counter = 0
        while True:
            suffix = f"_{counter}" if counter > 0 else ""
            image_path = date_dir / f"{base_name}{suffix}.png"
            meta_path = date_dir / f"{base_name}{suffix}.json"
            if not image_path.exists():
                break
            counter += 1

        return image_path, meta_path

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
    ) -> GenerateImageOutput:
        """Generate an image with Animagine XL 4.0.

        Args:
            prompt: The positive prompt (should be pre-validated/optimized)
            negative_prompt: Optional negative prompt (defaults applied if None)
            checkpoint: Checkpoint filename or 'default' (None uses current/default)
            loras: List of LoRA configs [{"filename": "...", "scale": 1.0}]
            width: Image width (default 832)
            height: Image height (default 1216)
            steps: Inference steps (default 28, use 4-8 with LCM)
            guidance_scale: Classifier-free guidance scale (default 5.0)
            seed: Random seed for reproducibility (random if None)

        Returns:
            GenerateImageOutput with image path and metadata
        """

        target_checkpoint = checkpoint or self._loaded_checkpoint or "default"
        if self._loaded_checkpoint != target_checkpoint or self._pipe is None:
            result = self.load_checkpoint(target_checkpoint)
            if not result["success"]:
                raise RuntimeError(f"Failed to load checkpoint: {result['message']}")


        if loras:
            self.unload_loras()
            for lora_config in loras:
                result = self.load_lora(
                    lora_config["filename"],
                    lora_config.get("scale", 1.0),
                )
                if not result["success"]:
                    raise RuntimeError(f"Failed to load LoRA: {result['message']}")


        final_negative = negative_prompt if negative_prompt else DEFAULT_NEGATIVE_PROMPT


        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        generator = torch.Generator(device=self.device).manual_seed(seed)


        result = self._pipe(
            prompt=prompt,
            negative_prompt=final_negative,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )

        image = result.images[0]


        image_path, meta_path = self._get_output_path()


        lora_configs = self._loaded_loras.copy()

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
            loras=lora_configs,
        )


        image.save(image_path)


        with open(meta_path, "w") as f:
            json.dump(metadata.model_dump(), f, indent=2)

        return GenerateImageOutput(
            image_path=str(image_path.absolute()),
            final_prompt=prompt,
            final_negative_prompt=final_negative,
            metadata=metadata,
        )

    def _load_source_image(self, image_path: str) -> Image.Image:
        """Load and prepare source image for img2img.

        Args:
            image_path: Path to source image

        Returns:
            PIL Image in RGB mode
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Source image not found: {image_path}")

        image = Image.open(path)
        if image.mode != "RGB":
            image = image.convert("RGB")
        return image

    def _get_img2img_pipeline(self):
        """Get or create an img2img pipeline from current text2img pipeline."""
        from diffusers import StableDiffusionXLImg2ImgPipeline

        if self._pipe is None:
            raise RuntimeError("No checkpoint loaded. Call load_checkpoint first.")


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
    ) -> GenerateImageOutput:
        """Generate an image using img2img (image-to-image) transformation.

        Args:
            image_path: Path to source image to transform
            prompt: The positive prompt describing desired output
            negative_prompt: Optional negative prompt (defaults applied if None)
            strength: Denoising strength (0.0-1.0). Higher = more change from source.
                     0.0 = no change, 1.0 = completely ignore source image.
                     Recommended: 0.3-0.5 for refinement, 0.6-0.8 for style transfer
            checkpoint: Checkpoint filename or 'default' (None uses current/default)
            loras: List of LoRA configs [{"filename": "...", "scale": 1.0}]
            steps: Inference steps (default 28, use 4-8 with LCM)
            guidance_scale: Classifier-free guidance scale (default 5.0)
            seed: Random seed for reproducibility (random if None)

        Returns:
            GenerateImageOutput with image path and metadata
        """

        target_checkpoint = checkpoint or self._loaded_checkpoint or "default"
        if self._loaded_checkpoint != target_checkpoint or self._pipe is None:
            result = self.load_checkpoint(target_checkpoint)
            if not result["success"]:
                raise RuntimeError(f"Failed to load checkpoint: {result['message']}")


        if loras:
            self.unload_loras()
            for lora_config in loras:
                result = self.load_lora(
                    lora_config["filename"],
                    lora_config.get("scale", 1.0),
                )
                if not result["success"]:
                    raise RuntimeError(f"Failed to load LoRA: {result['message']}")


        source_image = self._load_source_image(image_path)
        width, height = source_image.size


        img2img_pipe = self._get_img2img_pipeline()


        final_negative = negative_prompt if negative_prompt else DEFAULT_NEGATIVE_PROMPT


        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        generator = torch.Generator(device=self.device).manual_seed(seed)


        result = img2img_pipe(
            prompt=prompt,
            negative_prompt=final_negative,
            image=source_image,
            strength=strength,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )

        image = result.images[0]


        output_image_path, meta_path = self._get_output_path()


        lora_configs = self._loaded_loras.copy()

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
            loras=lora_configs,
            source_image=str(Path(image_path).absolute()),
            strength=strength,
        )


        image.save(output_image_path)


        with open(meta_path, "w") as f:
            json.dump(metadata.model_dump(), f, indent=2)

        return GenerateImageOutput(
            image_path=str(output_image_path.absolute()),
            final_prompt=prompt,
            final_negative_prompt=final_negative,
            metadata=metadata,
        )



_pipeline: AnimaginePipeline | None = None


def get_pipeline(output_dir: str | Path = "outputs") -> AnimaginePipeline:
    """Get or create the global pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = AnimaginePipeline(output_dir=output_dir)
    return _pipeline
