# Prompt Rulebook — Animagine MCP

Formal rules enforced by the MCP/Codex.

## Severities
- **ERROR**: blocks generation (or requires automatic correction).
- **WARNING**: allows generation but recommends adjustments.

## Core rules (MVP)

### RULE-01 (ERROR) — Quality tag required
The prompt MUST include at least one tag from the `quality` category (e.g., `masterpiece`).

### RULE-02 (WARNING→ERROR if repeated) — Quality tags last
Quality tags MUST appear at the end.  
If they appear elsewhere, the optimizer should move them to the end.

### RULE-03 (WARNING) — Short prompt
If the prompt has fewer than eight relevant tags, mark it as weak and suggest completing it with composition, environment, and style tags.

### RULE-04 (WARNING) — Character without series
If a character name is present without an associated series/origin, recommend adding one to improve consistency.

### RULE-05 (WARNING) — Mixed franchises/characters
If the prompt contains multiple series/origins or multiple characters, flag potential confusion.
Codex should ask about intent when the user does not mention “crossover/cosplay”.

### RULE-06 (WARNING) — Resolution outside presets
If `width*height` deviates significantly from the recommended presets (e.g., SDXL-friendly), warn about VRAM/time requirements and suggest alternatives.

### RULE-07 (INFO) — Apply default negative prompt
If `negative_prompt` is empty, apply the default and include it in the output.

## Canonical prompt order
1) gender_quantity  
2) character  
3) series_origin  
4) rating  
5) composition  
6) expression_pose  
7) appearance_clothing  
8) environment  
9) style_technique  
10) quality
