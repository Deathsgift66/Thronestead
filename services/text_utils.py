import re
import json
from pathlib import Path

_BANNED: set[str] = set()
try:
    _path = Path(__file__).resolve().parents[1] / "banned_words.json"
    with _path.open() as f:
        _BANNED = {w.lower() for w in json.load(f)}
except Exception:  # pragma: no cover - file may be missing in tests
    _BANNED = set()

_WORD_RE = re.compile(r"[^a-z0-9]+")

_TAG_RE = re.compile(r"<[^>]+>")


def sanitize_plain_text(text: str, max_length: int = 255) -> str:
    """Strip HTML tags, truncate to ``max_length`` and return clean text."""
    return _TAG_RE.sub("", text or "").strip()[:max_length]


def contains_banned_words(text: str | None) -> bool:
    """Return True if the normalized ``text`` includes a banned word."""
    normalized = _WORD_RE.sub("", text.lower()) if text else ""
    return any(b in normalized for b in _BANNED)
