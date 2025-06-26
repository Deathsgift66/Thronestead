"""Basic content moderation utilities."""

from __future__ import annotations

import re
from typing import Dict

from .text_utils import sanitize_plain_text

# Simplistic keyword sets for various categories
HATE_TERMS = {
    "nigger",
    "faggot",
    "kike",
    "dyke",
    "tranny",
}

SEXUAL_TERMS = {
    "porn",
    "sex",
    "anal",
    "dick",
    "pussy",
}

HARASSMENT_TERMS = {
    "kys",
    "kill",
    "dox",
}

PROFANITY_TERMS = {
    "fuck",
    "shit",
    "bitch",
}

TERRORISM_TERMS = {
    "isis",
    "kkk",
}

ILLEGAL_TERMS = {
    "drug",
    "hack",
    "weapon",
}

_SPAM_PATTERNS = [
    re.compile(r"https?://"),
    re.compile(r"(?:bit\.ly|tinyurl|t\.co|goo\.gl)", re.IGNORECASE),
]

_WORD_RE = re.compile(r"[a-z0-9]+")


def classify_text(text: str) -> Dict[str, bool]:
    """Return category flags for the given ``text``."""
    normalized = sanitize_plain_text(text).lower()
    tokens = set(_WORD_RE.findall(normalized))

    return {
        "hate_speech": bool(tokens & HATE_TERMS),
        "sexual_content": bool(tokens & SEXUAL_TERMS),
        "harassment": bool(tokens & HARASSMENT_TERMS),
        "profanity": bool(tokens & PROFANITY_TERMS),
        "terrorism": bool(tokens & TERRORISM_TERMS),
        "illegal_activity": bool(tokens & ILLEGAL_TERMS),
        "spam": any(p.search(text) for p in _SPAM_PATTERNS),
    }


def is_clean(text: str) -> bool:
    """Return True if ``text`` does not trigger any moderation rules."""
    return not any(classify_text(text).values())


RESERVED_USERNAMES = {"admin", "moderator", "mod", "developer", "dev"}


def has_reserved_username(username: str) -> bool:
    """Return True if ``username`` impersonates staff."""
    name = username.lower().replace("0", "o")
    return any(r in name for r in RESERVED_USERNAMES)
