"""Tag classification by category."""

import re
from enum import IntEnum


class TagCategory(IntEnum):
    """Tag categories in canonical order."""

    GENDER_QUANTITY = 1
    CHARACTER = 2
    SERIES_ORIGIN = 3
    RATING = 4
    COMPOSITION = 5
    EXPRESSION_POSE = 6
    APPEARANCE_CLOTHING = 7
    ENVIRONMENT = 8
    STYLE_TECHNIQUE = 9
    QUALITY = 10
    UNKNOWN = 99


                              
QUALITY_TAGS = {
    "masterpiece",
    "best quality",
    "high quality",
    "high score",
    "great score",
    "very aesthetic",
    "absurdres",
    "highres",
    "ultra detailed",
    "extremely detailed",
    "detailed",
}

GENDER_QUANTITY_PATTERNS = [
    r"^\d+girl[s]?$",
    r"^\d+boy[s]?$",
    r"^solo$",
    r"^multiple girls$",
    r"^multiple boys$",
    r"^couple$",
    r"^group$",
]

RATING_TAGS = {
    "safe",
    "sensitive",
    "nsfw",
    "general",
    "questionable",
    "explicit",
    "sfw",
}

COMPOSITION_TAGS = {
    "looking at viewer",
    "looking away",
    "from above",
    "from below",
    "from side",
    "from behind",
    "full body",
    "upper body",
    "lower body",
    "cowboy shot",
    "portrait",
    "close-up",
    "dutch angle",
    "wide shot",
    "medium shot",
    "profile",
    "three-quarter view",
}

EXPRESSION_POSE_TAGS = {
    "smile",
    "smiling",
    "grin",
    "open mouth",
    "closed mouth",
    "closed eyes",
    "half-closed eyes",
    "wink",
    "blush",
    "crying",
    "tears",
    "angry",
    "sad",
    "happy",
    "surprised",
    "embarrassed",
    "standing",
    "sitting",
    "lying",
    "kneeling",
    "walking",
    "running",
    "jumping",
    "arms up",
    "arms crossed",
    "hand on hip",
    "peace sign",
    "v sign",
    "pointing",
    "waving",
}

ENVIRONMENT_TAGS = {
    "outdoors",
    "indoors",
    "outside",
    "inside",
    "simple background",
    "white background",
    "black background",
    "gradient background",
    "blue sky",
    "night",
    "day",
    "sunset",
    "sunrise",
    "beach",
    "forest",
    "city",
    "school",
    "classroom",
    "bedroom",
    "kitchen",
    "bathroom",
    "street",
    "park",
    "garden",
    "ocean",
    "mountains",
    "snow",
    "rain",
}

STYLE_TECHNIQUE_TAGS = {
    "anime",
    "manga",
    "illustration",
    "digital art",
    "watercolor",
    "sketch",
    "lineart",
    "cel shading",
    "flat color",
    "soft lighting",
    "dramatic lighting",
    "backlighting",
    "rim lighting",
    "cinematic",
    "photorealistic",
    "painterly",
    "vibrant colors",
    "muted colors",
    "monochrome",
    "sepia",
}

                                                  
KNOWN_SERIES = {
    "genshin impact",
    "honkai star rail",
    "honkai impact",
    "fate/grand order",
    "fate/stay night",
    "blue archive",
    "arknights",
    "azur lane",
    "kantai collection",
    "hololive",
    "nijisanji",
    "vtuber",
    "original",
    "pokemon",
    "naruto",
    "one piece",
    "demon slayer",
    "jujutsu kaisen",
    "my hero academia",
    "attack on titan",
    "spy x family",
    "bocchi the rock",
    "chainsaw man",
    "frieren",
    "oshi no ko",
}


def classify_tag(tag: str) -> TagCategory:
    """Classify a tag into its category."""
    tag_lower = tag.lower().strip()

                  
    if tag_lower in QUALITY_TAGS:
        return TagCategory.QUALITY

                              
    for pattern in GENDER_QUANTITY_PATTERNS:
        if re.match(pattern, tag_lower):
            return TagCategory.GENDER_QUANTITY

            
    if tag_lower in RATING_TAGS:
        return TagCategory.RATING

                 
    if tag_lower in COMPOSITION_TAGS:
        return TagCategory.COMPOSITION

                     
    if tag_lower in EXPRESSION_POSE_TAGS:
        return TagCategory.EXPRESSION_POSE

                 
    if tag_lower in ENVIRONMENT_TAGS:
        return TagCategory.ENVIRONMENT

                     
    if tag_lower in STYLE_TECHNIQUE_TAGS:
        return TagCategory.STYLE_TECHNIQUE

                                                   
    if tag_lower in KNOWN_SERIES:
        return TagCategory.SERIES_ORIGIN

                                                                                      
                                                               
    if "(" in tag_lower and ")" in tag_lower:
                                                                        
        return TagCategory.CHARACTER

                                                                  
    return TagCategory.UNKNOWN


def is_quality_tag(tag: str) -> bool:
    """Check if a tag is a quality tag."""
    return classify_tag(tag) == TagCategory.QUALITY


def is_series_tag(tag: str) -> bool:
    """Check if a tag appears to be a series/origin."""
    return tag.lower().strip() in KNOWN_SERIES


def extract_series_from_character(tag: str) -> str | None:
    """Extract series name from character tag like 'ganyu (genshin impact)'."""
    match = re.search(r"\(([^)]+)\)", tag)
    if match:
        return match.group(1).strip()
    return None
