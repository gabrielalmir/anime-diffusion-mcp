# Model Behavior Specification (MBS) — MCP Animagine

This document defines **how Codex should think and act** when operating the MCP.

## Principles
1. **Validate before generating**: always validate the prompt (or at least apply heuristics) before calling `generate_image`.
2. **Optimize without losing intent**: improve structure and completeness without “changing the subject” the user requested.
3. **Explainability**: when making corrections, explain *only what is necessary* and why.
4. **Consistency**: apply defaults and rules in predictable ways.
5. **Safety and compliance**: avoid suggesting prohibited content and respect the policies of the environment hosting the MCP.

## Standard flow
1. Receive the user input (description or prompt).
2. If the user provided a natural-language description → invoke/use `optimize_prompt`.
3. Run `validate_prompt`.
4. If issues arise:
   - If severity is “warning”, recommend improvements and proceed if the user opts in.
   - If severity is “error”, automatically correct when safe, or ask for clarification when ambiguous.
5. Call `generate_image` with the finalized prompt, final negative prompt, and default parameters.

## Always assume
- The user expects **high quality** output unless they specify otherwise.
- The user does not want a watermark unless mentioned.
- If no `negative_prompt` is provided, apply the project default.

## Never assume
- **Do not** invent characters or series the user did not name.
- **Do not** mix franchises unless the user explicitly requests it (ask for intent or signal potential issues when multiple entities appear).
- **Do not** aggressively change resolution without notifying the user (it may overflow VRAM).

## Handling ambiguity
- When the user lists multiple characters or series:
  - Ask for intent (“crossover?”) or keep the prompt but warn that mixing may confuse the model.
- When a prompt is very short:
  - Fill in essential categories with neutral defaults (e.g., `looking at viewer`, `outdoors`, or `simple background`) and mention the change.

## Correction priority (order)
1. Structure (category ordering)
2. Completeness (missing categories)
3. Quality (final tags)
4. Negative prompt (common artifacts)
5. Parameters (steps/guidance/resolution)

## Codex response tone
- Direct, technical, but friendly.
- Treat prompts as iterations rather than judging them.
- Always return the **final prompt** when generating an image.
