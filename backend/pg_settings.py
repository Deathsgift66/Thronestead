from fastapi import Request
import json
import logging

try:
    import jwt  # PyJWT
except Exception:  # pragma: no cover - fallback to python-jose
    from jose import jwt  # type: ignore

logger = logging.getLogger("KingmakersRise.PGSettings")


def inject_claims_as_pg_settings(request: Request) -> dict[str, str]:
    """Return session-level PostgreSQL settings derived from the user's JWT."""
    user = getattr(request.state, "user", None)
    token = getattr(user, "token", None)
    if not token:
        return {}
    try:
        jwt_claims = jwt.decode(token, options={"verify_signature": False})
    except Exception:  # pragma: no cover - decode issues shouldn't crash request
        logger.exception("Failed to decode JWT for pg settings")
        return {}
    return {"request.jwt.claims": json.dumps(jwt_claims)}
