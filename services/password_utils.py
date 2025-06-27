import hashlib
import logging
import httpx

logger = logging.getLogger("Thronestead.PasswordSecurity")


def is_password_breached(password: str) -> bool:
    """Return True if the password appears in a known breach database."""
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        resp = httpx.get(
            f"https://api.pwnedpasswords.com/range/{prefix}",
            timeout=5,
        )
        resp.raise_for_status()
    except Exception:  # pragma: no cover - network errors
        logger.exception("Failed to query breach API")
        return False
    for line in resp.text.splitlines():
        if ":" not in line:
            continue
        hash_suffix, _count = line.split(":", 1)
        if hash_suffix.upper() == suffix:
            return True
    return False
