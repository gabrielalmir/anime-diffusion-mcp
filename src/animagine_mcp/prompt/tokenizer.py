"""Prompt tokenization utilities."""

import re


def tokenize_prompt(prompt: str) -> list[str]:
    """Split a prompt into individual tags.

    Handles comma-separated tags and normalizes whitespace.
    """
    if not prompt or not prompt.strip():
        return []

                    
    tags = prompt.split(",")

                                                                 
    cleaned = []
    for tag in tags:
        tag = tag.strip()
                                                   
        tag = re.sub(r"\s+", " ", tag)
        if tag:
            cleaned.append(tag.lower())

    return cleaned


def join_tags(tags: list[str]) -> str:
    """Join tags back into a comma-separated prompt."""
    return ", ".join(tags)
