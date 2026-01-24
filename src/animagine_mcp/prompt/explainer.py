"""Prompt explanation utilities."""

from ..contracts import ExplainPromptOutput, TagExplanation
from .tokenizer import tokenize_prompt, join_tags
from .classifier import classify_tag, TagCategory


                             
TAG_EXPLANATIONS: dict[str, str] = {
             
    "masterpiece": "Highest quality indicator, prioritizes detailed and polished output",
    "best quality": "Quality boost tag for refined generation",
    "high quality": "General quality improvement tag",
    "high score": "Animagine-specific quality tag for better aesthetics",
    "great score": "Animagine-specific tag for improved visual quality",
    "absurdres": "Extremely high resolution/detail level",
    "highres": "High resolution output",

                     
    "1girl": "Single female character",
    "1boy": "Single male character",
    "2girls": "Two female characters",
    "2boys": "Two male characters",
    "solo": "Single character focus",
    "multiple girls": "More than one female character",
    "multiple boys": "More than one male character",

                 
    "looking at viewer": "Character faces the camera/viewer",
    "looking away": "Character looks away from the viewer",
    "from above": "Bird's eye view perspective",
    "from below": "Low angle perspective",
    "from side": "Side profile view",
    "from behind": "Back view of character",
    "full body": "Shows entire character from head to toe",
    "upper body": "Shows character from waist up",
    "cowboy shot": "Framing from mid-thigh up",
    "portrait": "Head and shoulders focus",
    "close-up": "Tight framing on face/details",

                 
    "outdoors": "Outdoor setting/background",
    "indoors": "Indoor setting/background",
    "simple background": "Minimal, undetailed background",
    "white background": "Plain white backdrop",
    "black background": "Plain black backdrop",
    "gradient background": "Smooth color transition background",
    "blue sky": "Clear sky as background element",
    "night": "Nighttime setting",
    "day": "Daytime setting",

                     
    "smile": "Character is smiling",
    "open mouth": "Character's mouth is open",
    "closed eyes": "Character's eyes are closed",
    "blush": "Character has reddened cheeks",
    "standing": "Character is in standing pose",
    "sitting": "Character is in sitting pose",

           
    "anime": "Anime art style",
    "illustration": "Illustration style rendering",
    "digital art": "Digital artwork style",
    "cinematic": "Movie-like dramatic composition",
    "soft lighting": "Gentle, diffused lighting",
    "dramatic lighting": "High contrast, bold lighting",

            
    "safe": "Safe for work content",
    "general": "General audience appropriate",
}

CATEGORY_NAMES: dict[TagCategory, str] = {
    TagCategory.GENDER_QUANTITY: "Gender/Quantity",
    TagCategory.CHARACTER: "Character",
    TagCategory.SERIES_ORIGIN: "Series/Origin",
    TagCategory.RATING: "Rating",
    TagCategory.COMPOSITION: "Composition",
    TagCategory.EXPRESSION_POSE: "Expression/Pose",
    TagCategory.APPEARANCE_CLOTHING: "Appearance/Clothing",
    TagCategory.ENVIRONMENT: "Environment",
    TagCategory.STYLE_TECHNIQUE: "Style/Technique",
    TagCategory.QUALITY: "Quality",
    TagCategory.UNKNOWN: "Other",
}


def explain_prompt(prompt: str) -> ExplainPromptOutput:
    """Explain what each tag in a prompt does.

    Returns a breakdown of each tag with its category and explanation,
    plus the prompt reordered in canonical form.
    """
    tags = tokenize_prompt(prompt)

    if not tags:
        return ExplainPromptOutput(
            breakdown=[],
            ordered_prompt=None,
        )

    breakdown: list[TagExplanation] = []
    classified: dict[TagCategory, list[str]] = {cat: [] for cat in TagCategory}

    for tag in tags:
        category = classify_tag(tag)
        classified[category].append(tag)

                         
        explanation = TAG_EXPLANATIONS.get(
            tag.lower(),
            _generate_explanation(tag, category),
        )

        breakdown.append(
            TagExplanation(
                tag=tag,
                category=CATEGORY_NAMES.get(category, "Unknown"),
                explanation=explanation,
            )
        )

                          
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
        TagCategory.UNKNOWN,
        TagCategory.QUALITY,                      
    ]

    ordered_tags: list[str] = []
    for category in category_order:
        ordered_tags.extend(classified[category])

    ordered_prompt = join_tags(ordered_tags) if ordered_tags else None

    return ExplainPromptOutput(
        breakdown=breakdown,
        ordered_prompt=ordered_prompt,
    )


def _generate_explanation(tag: str, category: TagCategory) -> str:
    """Generate a basic explanation for unknown tags."""
    category_hints = {
        TagCategory.CHARACTER: f"Character name: '{tag}'",
        TagCategory.SERIES_ORIGIN: f"From series/franchise: '{tag}'",
        TagCategory.APPEARANCE_CLOTHING: f"Describes appearance or clothing: '{tag}'",
        TagCategory.UNKNOWN: f"Custom tag: '{tag}' (may affect style/content)",
    }

    return category_hints.get(
        category,
        f"Tag that influences the {CATEGORY_NAMES.get(category, 'output').lower()}",
    )
