# Implementation Guide — Diffusers + Animagine XL 4.0

## Dependencies
```bash
pip install diffusers transformers accelerate safetensors --upgrade
```

## Base pipeline (per requirements)
```python
import torch
from diffusers import StableDiffusionXLPipeline

pipe = StableDiffusionXLPipeline.from_pretrained(
    "cagliostrolab/animagine-xl-4.0",
    torch_dtype=torch.float16,
    use_safetensors=True,
    custom_pipeline="lpw_stable_diffusion_xl",
    add_watermarker=False
)
pipe.to("cuda")
```

## Generation example
```python
prompt = "1girl, ... , masterpiece, high score, great score, absurdres"
negative_prompt = "lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, fewer digits, cropped, worst quality, low quality, low score, bad score, average score, signature, watermark, username, blurry"

image = pipe(
    prompt,
    negative_prompt=negative_prompt,
    width=832,
    height=1216,
    guidance_scale=5,
    num_inference_steps=28
).images[0]

image.save("./output.png")
```

## Recommended observability
Whenever you save the generated image, also write a JSON payload alongside it that contains:
- final prompt
- final negative prompt
- seed
- resolution
- steps/guidance
