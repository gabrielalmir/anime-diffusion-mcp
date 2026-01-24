"""Prompt validation against Animagine XL rules."""

from ..contracts import Issue, Severity, ValidatePromptOutput
from ..contracts.errors import ErrorCode
from .tokenizer import tokenize_prompt
from .classifier import (
    classify_tag,
    is_quality_tag,
    is_series_tag,
    extract_series_from_character,
    TagCategory,
    KNOWN_SERIES,
)


                                       
RECOMMENDED_RESOLUTIONS = [
    (832, 1216),             
    (1216, 832),              
    (1024, 1024),          
    (896, 1152),                  
    (1152, 896),                   
]

MIN_TAG_COUNT = 8


def validate_prompt(
    prompt: str,
    width: int = 832,
    height: int = 1216,
    negative_prompt: str | None = None,
) -> ValidatePromptOutput:
    """Validate a prompt against Animagine XL rules.

    Implements:
    - RULE-01: Quality tag required (ERROR)
    - RULE-02: Quality tags at end (WARNING)
    - RULE-03: Minimum 8 tags (WARNING)
    - RULE-04: Character needs series (WARNING)
    - RULE-05: Multiple series warning (WARNING)
    - RULE-06: Resolution preset check (WARNING)
    - RULE-07: Default negative prompt info (INFO)
    """
    issues: list[Issue] = []
    suggestions: list[str] = []

    tags = tokenize_prompt(prompt)

    if not tags:
        issues.append(
            Issue(
                code=ErrorCode.PROMPT_TOO_SHORT,
                severity=Severity.ERROR,
                message="Prompt is empty",
                hint="Provide at least some tags describing the image",
            )
        )
        return ValidatePromptOutput(valid=False, issues=issues, suggestions=suggestions)

                                   
    quality_tags = [t for t in tags if is_quality_tag(t)]
    if not quality_tags:
        issues.append(
            Issue(
                code=ErrorCode.PROMPT_MISSING_QUALITY_TAG,
                severity=Severity.ERROR,
                message="No quality tag found",
                hint="Add 'masterpiece' or 'best quality' to improve results",
            )
        )

                                                
    if quality_tags:
        quality_indices = [i for i, t in enumerate(tags) if is_quality_tag(t)]
        non_quality_count = len(tags) - len(quality_tags)

                                                                  
        if quality_indices and min(quality_indices) < non_quality_count:
            issues.append(
                Issue(
                    code=ErrorCode.PROMPT_QUALITY_NOT_LAST,
                    severity=Severity.WARNING,
                    message="Quality tags should be at the end of the prompt",
                    hint="Move quality tags like 'masterpiece' to the end",
                )
            )

                                
    if len(tags) < MIN_TAG_COUNT:
        issues.append(
            Issue(
                code=ErrorCode.PROMPT_TOO_SHORT,
                severity=Severity.WARNING,
                message=f"Prompt has only {len(tags)} tags (minimum {MIN_TAG_COUNT} recommended)",
                hint="Add more tags for composition, environment, and style",
            )
        )
        suggestions.append("Consider adding: composition (looking at viewer), environment (outdoors/indoors), style tags")

                                                  
    character_tags = []
    series_tags = []

    for tag in tags:
        category = classify_tag(tag)
        if category == TagCategory.CHARACTER:
            character_tags.append(tag)
                                                          
            embedded_series = extract_series_from_character(tag)
            if embedded_series:
                series_tags.append(embedded_series)
        elif category == TagCategory.SERIES_ORIGIN:
            series_tags.append(tag)

                                               
    for tag in tags:
        if is_series_tag(tag) and tag.lower() not in [s.lower() for s in series_tags]:
            series_tags.append(tag)

                                       
    if character_tags and not series_tags:
                                                
        has_embedded = any(extract_series_from_character(c) for c in character_tags)
        if not has_embedded:
            issues.append(
                Issue(
                    code=ErrorCode.PROMPT_CHARACTER_NO_SERIES,
                    severity=Severity.WARNING,
                    message="Character name without series/origin",
                    hint="Add the series name or use format 'character (series)'",
                )
            )
            suggestions.append("Adding the series/origin improves character consistency")

                              
    unique_series = set(s.lower() for s in series_tags)
    if len(unique_series) > 1:
        issues.append(
            Issue(
                code=ErrorCode.PROMPT_MULTIPLE_SERIES,
                severity=Severity.WARNING,
                message=f"Multiple series detected: {', '.join(unique_series)}",
                hint="Consider if this is intentional (crossover) or might confuse the model",
            )
        )

                               
    resolution = (width, height)
    if resolution not in RECOMMENDED_RESOLUTIONS:
                                                       
        total_pixels = width * height
        if total_pixels > 1024 * 1024 * 1.5:                           
            issues.append(
                Issue(
                    code=ErrorCode.PARAM_RESOLUTION_RISK,
                    severity=Severity.WARNING,
                    message=f"Resolution {width}x{height} may cause VRAM issues",
                    hint="Use 832x1216 (portrait), 1024x1024 (square), or 1216x832 (landscape)",
                )
            )

                                           
    if not negative_prompt:
        issues.append(
            Issue(
                code=ErrorCode.DEFAULT_NEGATIVE_APPLIED,
                severity=Severity.INFO,
                message="No negative prompt provided",
                hint="Default negative prompt will be applied",
            )
        )

                                                              
    has_errors = any(issue.severity == Severity.ERROR for issue in issues)

    return ValidatePromptOutput(
        valid=not has_errors,
        issues=issues,
        suggestions=suggestions,
    )
