# Reasoning & Correction Guidelines

## Goal
Standardize how Codex fixes poor prompts without losing user intent.

## High-level algorithm
1. **Tokenize** the prompt into tags.
2. **Classify** tags by category (taxonomy).
3. **Detect gaps** in essential categories.
4. **Normalize order** (canonical ordering).
5. **Supplement** with neutral tags when needed:
   - composition: `looking at viewer` (if appropriate) or `portrait`
   - environment: `outdoors` or `indoors` (favor what the user indicates)
6. **Ensure quality tags are last**.
7. **Generate a report** describing what changed and why.

## Helpful heuristics
- When `night` is present and neither `outdoors` nor `indoors` is specified, suggest `outdoors` by default.
- When `solo` appears alongside `2girls`, remove `solo` (conflicting) and emit a WARNING.
- When there are many clothing tags without pose/composition, suggest `upper body` or `full body`.

## When to ask the user
- Mixed franchises plus different characters without “cosplay/crossover.”
- Contradictory style labels (e.g., “realistic photo” + “anime coloring”).
- Very high resolutions without a GPU/VRAM indication.

## Explanation format (concise and actionable)
- “Moved `masterpiece` to the end (RULE-02).”
- “Added `outdoors` to complete the environment (RULE-03).”
