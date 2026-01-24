# Configuration & Defaults Spec — Animagine MCP

## Defaults (MVP)
- model_id: `cagliostrolab/animagine-xl-4.0`
- torch_dtype: float16
- use_safetensors: true
- custom_pipeline: `lpw_stable_diffusion_xl`
- add_watermarker: false
- device: `cuda` (preferred)

## Generation parameters
- width: 832
- height: 1216
- steps: 28
- guidance_scale: 5
- seed: null (if null, generate random seed and return it in the metadata)

## Default negative prompt
```
lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, fewer digits,
cropped, worst quality, low quality, low score, bad score, average score, signature,
watermark, username, blurry
```

## Recommended presets (SDXL-friendly)
- 832x1216 (portrait)
- 1024x1024 (square)
- 1216x832 (landscape)

## Fallback policy (optional)
- If CUDA is unavailable: allow CPU with a WARNING (slow) or fail with an error (configurable).
