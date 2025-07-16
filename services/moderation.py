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
# These patterns intentionally cover common formats to help prevent
# younger users from sharing contact details in violation of
# COPPA/GDPR-K guidelines.
_PERSONAL_INFO_PATTERNS = [
    # Standard email addresses
    re.compile(r"[\w.-]+@[\w.-]+\.[a-z]{2,}", re.IGNORECASE),
    # 10+ digit sequences with optional separators or country code
    re.compile(
        r"(?:\+?\d{1,3}[ -]?)?(?:\(?\d{3}\)?[ -]?\d{3}[ -]?\d{4})",
        re.IGNORECASE,
    ),
]

_WORD_RE = re.compile(r"[a-z0-9]+")


def classify_text(text: str) -> Dict[str, bool]:
    """Return category flags for the given ``text``."""
    cleaned = sanitize_plain_text(text)
    lowered = cleaned.lower()
    tokens = set(_WORD_RE.findall(lowered))

    return {
        "hate_speech": bool(tokens & HATE_TERMS),
        "sexual_content": bool(tokens & SEXUAL_TERMS),
        "harassment": bool(tokens & HARASSMENT_TERMS),
        "profanity": bool(tokens & PROFANITY_TERMS),
        "terrorism": bool(tokens & TERRORISM_TERMS),
        "illegal_activity": bool(tokens & ILLEGAL_TERMS),
        "spam": any(p.search(cleaned) for p in _SPAM_PATTERNS),
        "personal_info": any(p.search(cleaned) for p in _PERSONAL_INFO_PATTERNS),
        "malicious_link": any(d in lowered for d in MALICIOUS_DOMAINS),
    }


def is_clean(text: str) -> bool:
    """Return True if ``text`` does not trigger any moderation rules."""
    return not any(classify_text(text).values())


def contains_malicious_link(text: str) -> bool:
    """Return True if ``text`` contains links to blocked domains."""
    lowered = text.lower()
    return any(d in lowered for d in MALICIOUS_DOMAINS)


RESERVED_USERNAMES = {"admin", "moderator", "mod", "developer", "dev"}
RESERVED_KINGDOM_NAMES = {"admin", "moderator", "support"}


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


def has_reserved_kingdom_name(name: str) -> bool:
    """Return True if ``name`` impersonates staff or reserved strings."""
    normalized = name.lower().replace("0", "o")
    return any(r in normalized for r in RESERVED_KINGDOM_NAMES)


def validate_kingdom_name(name: str) -> None:
    """Validate a kingdom name for length, characters and reserved terms."""
    validate_clean_text(name)
    if not (3 <= len(name) <= 32):
        raise ValueError("Kingdom name must be 3-32 characters")
    if not re.fullmatch(r"[A-Za-z0-9 _'-]+", name):
        raise ValueError("Kingdom name contains invalid characters")
    if has_reserved_kingdom_name(name):
        raise ValueError("Kingdom name contains reserved term")
