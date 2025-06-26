"""Basic content moderation utilities."""

from __future__ import annotations

import re
from typing import Dict

from .text_utils import sanitize_plain_text, contains_banned_words

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

# Basic list of domains to block outright
MALICIOUS_DOMAINS = {"example.com", "malware.test"}

# Basic patterns for personal information (emails, phone numbers)
_PERSONAL_INFO_PATTERNS = [
    re.compile(r"\b\d{10}\b"),  # 10 digit numbers
    re.compile(r"[\w.-]+@[\w.-]+\.[a-z]{2,}", re.IGNORECASE),
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
        "personal_info": any(p.search(text) for p in _PERSONAL_INFO_PATTERNS),
        "malicious_link": any(d in text.lower() for d in MALICIOUS_DOMAINS),
    }


def is_clean(text: str) -> bool:
    """Return True if ``text`` does not trigger any moderation rules."""
    return not any(classify_text(text).values())


def contains_malicious_link(text: str) -> bool:
    """Return True if ``text`` contains links to blocked domains."""
    lower = text.lower()
    return any(d in lower for d in MALICIOUS_DOMAINS)


RESERVED_USERNAMES = {"admin", "moderator", "mod", "developer", "dev"}


def has_reserved_username(username: str) -> bool:
    """Return True if ``username`` impersonates staff."""
    name = username.lower().replace("0", "o")
    return any(r in name for r in RESERVED_USERNAMES)


def flag_violations(text: str) -> list[str]:
    """Return a list of moderation categories triggered by ``text``."""
    if contains_banned_words(text):
        return ["banned_words"]
    flags = classify_text(text)
    return [key for key, value in flags.items() if value]


def validate_clean_text(text: str) -> None:
    """Raise ``ValueError`` if ``text`` violates any moderation rule."""
    violations = flag_violations(text)
    if violations:
        raise ValueError(
            "Input violates policy: " + ", ".join(sorted(violations))
        )


def validate_username(username: str) -> None:
    """Validate a username against banned words and reserved terms."""
    validate_clean_text(username)
    if has_reserved_username(username):
        raise ValueError("Username contains reserved term")
