# MCP Interface Contract — Animagine XL

This document defines the MCP tools and their contracts.

## Tool: generate_image
### Input (JSON)
- prompt: string (required)
- negative_prompt: string (optional)
- width: int (default 832)
- height: int (default 1216)
- steps: int (default 28)
- guidance_scale: float (default 5)
- seed: int|null (default null)

### Output (JSON)
- image_path: string
- final_prompt: string
- final_negative_prompt: string
- metadata: object (steps, guidance_scale, width, height, seed, model_id, pipeline)

## Tool: optimize_prompt
### Input
- description: string (natural language description) OR prompt: string (raw prompt)

### Output
- optimized_prompt: string
- actions: [string] (list of applied transformations)
- warnings: [string]

## Tool: validate_prompt
### Input
- prompt: string

### Output
- valid: bool
- issues: [{code, severity, message, hint}]
- suggestions: [string]

## Tool: explain_prompt
### Input
- prompt: string

### Output
- breakdown: { tag: explanation }
- ordered_prompt: string (optional)
