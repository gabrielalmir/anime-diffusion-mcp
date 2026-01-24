"""Prompt optimization for Animagine XL."""

from ..contracts import OptimizePromptOutput
from .tokenizer import tokenize_prompt, join_tags
from .classifier import classify_tag, TagCategory, is_quality_tag


                                                 
DEFAULT_COMPOSITION = "looking at viewer"
DEFAULT_ENVIRONMENT = "simple background"
DEFAULT_QUALITY = ["masterpiece", "high score", "great score", "absurdres"]


def optimize_prompt(
    description: str | None = None,
    prompt: str | None = None,
) -> OptimizePromptOutput:
    """Optimize a prompt for Animagine XL.

    Can accept either:
    - description: Natural language description to convert to tags
    - prompt: Existing tag-based prompt to optimize

    Actions performed:
    - Reorder tags by canonical category order
    - Move quality tags to the end
    - Add missing essential categories with neutral defaults
    """
    actions: list[str] = []
    warnings: list[str] = []

                          
    if description and not prompt:
                                           
                                                                                     
        input_text = description
        actions.append("Processed natural language description")
        warnings.append("Natural language conversion is basic; consider providing tags directly")
    elif prompt:
        input_text = prompt
    else:
        return OptimizePromptOutput(
            optimized_prompt="",
            actions=["No input provided"],
            warnings=["Provide either 'description' or 'prompt'"],
        )

    tags = tokenize_prompt(input_text)

    if not tags:
        return OptimizePromptOutput(
            optimized_prompt="",
            actions=["Empty prompt"],
            warnings=["No tags found in input"],
        )

                       
    classified: dict[TagCategory, list[str]] = {cat: [] for cat in TagCategory}
    for tag in tags:
        category = classify_tag(tag)
        classified[category].append(tag)

                       
    added_tags: list[str] = []

                                             
    if not classified[TagCategory.COMPOSITION]:
        classified[TagCategory.COMPOSITION].append(DEFAULT_COMPOSITION)
        added_tags.append(DEFAULT_COMPOSITION)
        actions.append(f"Added default composition: {DEFAULT_COMPOSITION}")

                                             
    if not classified[TagCategory.ENVIRONMENT]:
        classified[TagCategory.ENVIRONMENT].append(DEFAULT_ENVIRONMENT)
        added_tags.append(DEFAULT_ENVIRONMENT)
        actions.append(f"Added default environment: {DEFAULT_ENVIRONMENT}")

                                      
    if not classified[TagCategory.QUALITY]:
        classified[TagCategory.QUALITY].extend(DEFAULT_QUALITY)
        added_tags.extend(DEFAULT_QUALITY)
        actions.append(f"Added quality tags: {', '.join(DEFAULT_QUALITY)}")

                                       
    ordered_tags: list[str] = []

                                                                          
    category_order = [
        TagCategory.GENDER_QUANTITY,
        TagCategory.CHARACTER,
        TagCategory.SERIES_ORIGIN,
        TagCategory.RATING,
        TagCategory.COMPOSITION,
        TagCategory.EXPRESSION_POSE,
        TagCategory.APPEARANCE_CLOTHING,
        TagCategory.ENVIRONMENT,
        TagCategory.STYLE_TECHNIQUE,
    ]

    for category in category_order:
        ordered_tags.extend(classified[category])

                                                                   
    ordered_tags.extend(classified[TagCategory.UNKNOWN])

                             
    ordered_tags.extend(classified[TagCategory.QUALITY])

                                  
    original_order = tags
    if ordered_tags != original_order:
        actions.append("Reordered tags by canonical category order")

    optimized = join_tags(ordered_tags)

    return OptimizePromptOutput(
        optimized_prompt=optimized,
        actions=actions if actions else ["No changes needed"],
        warnings=warnings,
    )
