"""
Project: Thronestead ©
File: pg_settings.py
Role: PostgreSQL configuration helper.
Version: 2025-06-21
"""

import json
import logging

from fastapi import Request
from jose import JWTError

logger = logging.getLogger("Thronestead.PGSettings")


def inject_claims_as_pg_settings(request: Request) -> dict[str, str]:
    """Return session-level PostgreSQL settings derived from the user's JWT."""
    from .security import decode_supabase_jwt
    user = getattr(request.state, "user", None)
    claims = getattr(user, "claims", None)
    if claims is None:
        token = getattr(user, "token", None)
        if not token:
            return {}
        try:
            claims = decode_supabase_jwt(token)
        except JWTError:  # pragma: no cover - decode issues shouldn't crash request
            logger.exception("Failed to decode JWT for pg settings")
            return {}
    return {"request.jwt.claims": json.dumps(claims)}
