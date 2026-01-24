# Quality Evaluation Guide — Animagine MCP

## Goal
Define practical criteria to judge output quality and guide adjustments.

## Visual checklist (common in anime diffusion)
- Hands: extra/missing fingers, deformation
- Eyes: asymmetry, “melted” look
- Text/signature: watermark, username
- Overall anatomy: odd arms/necks
- Background: noise, artifacts, excessive blur
- Cropping: head cut off, subject outside the frame

## Quick mapping: problem → action
- Poor hands → reinforce the negative prompt (`bad hands`), tweak the pose, or slightly raise steps
- Washed-out image → bump guidance (e.g., 5 → 6) or add lighting/style tags
- Too stiff/no variation → lower guidance (e.g., 5 → 4.5) or change the seed
- Confusing background → add `simple background` or clarify the environment

## Tuning recommendations
- steps: 20–35 (more steps increase runtime, not always quality)
- guidance: 4–7 (too high guidance can “lock” creativity and introduce artifacts)
- resolution: increase carefully (VRAM sensitive)
