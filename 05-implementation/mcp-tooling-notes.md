# MCP Tooling Notes — Exposing to Codex

## Recommended design
- Codex calls MCP tools with simple JSON.
- MCP returns file paths and metadata.
- Separate modules:
  - `prompt/` (tokenize, classify, reorder, lint, optimize)
  - `diffusion/` (load pipeline, generate)
  - `contracts/` (schemas and error codes)

## Recommended sequence
1) validate_prompt
2) optimize_prompt (if needed)
3) validate_prompt (again, post-optimization)
4) generate_image

## Persistence
- Use `outputs/YYYY-MM-DD/` folders containing:
  - `image.png`
  - `image.json` (metadata)
