import re

_TAG_RE = re.compile(r"<[^>]+>")


def sanitize_plain_text(text: str, max_length: int = 255) -> str:
    """Strip HTML tags, truncate to ``max_length`` and return clean text."""
    cleaned = _TAG_RE.sub("", text or "").strip()
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned

