import hashlib
import logging
import httpx


def is_pwned_password(password: str) -> bool:
    """Check the given password against the Pwned Passwords database."""
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        resp = httpx.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5)
        resp.raise_for_status()
        for line in resp.text.splitlines():
            h, _ = line.split(":", 1)
            if h == suffix:
                return True
    except Exception:  # pragma: no cover - external call
        logging.getLogger("Thronestead.PasswordSecurity").exception(
            "Pwned password lookup failed"
        )
    return False
