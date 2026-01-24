# Error Handling & Diagnostics Spec — Animagine MCP

## Purpose
Standardize errors and warnings so Codex never invents response formats.

## Issue structure
```json
{
  "code": "PROMPT_RULE_VIOLATION",
  "severity": "error | warning | info",
  "message": "Short, clear text",
  "hint": "How to fix in one sentence"
}
```

## Suggested codes
- PROMPT_MISSING_QUALITY_TAG (error)
- PROMPT_QUALITY_NOT_LAST (warning)
- PROMPT_TOO_SHORT (warning)
- PROMPT_MULTIPLE_SERIES (warning)
- PROMPT_CONFLICTING_TAGS (warning)
- PARAM_RESOLUTION_RISK (warning)
- PIPELINE_INIT_FAILED (error)
- CUDA_NOT_AVAILABLE (error|warning depending on fallback)
- OUT_OF_MEMORY (error)

## Message rules
- No long paragraphs
- Do not blame the user
- Always include a hint when severity != info
