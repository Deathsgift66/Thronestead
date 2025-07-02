import hashlib
import logging
import httpx


def is_pwned_password(password: str) -> bool:
    """Check the given password against the Pwned Passwords database."""
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        resp = httpx.get(
            f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5
        )
        resp.raise_for_status()
        return any(
            line.split(":", 1)[0] == suffix for line in resp.text.splitlines()
        )
    except Exception:  # pragma: no cover - external call
        logging.getLogger("Thronestead.PasswordSecurity").exception(
            "Pwned password lookup failed"
        )
    return False
