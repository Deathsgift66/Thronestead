# Project Name: Thronestead©
# File Name: security.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Handles header-based user validation using Supabase-issued JWT tokens.

Lightweight decoding for in-request matching.
Signature validation is expected to be handled by Supabase middleware/gateway.
"""

import base64
import json
import os
from uuid import UUID
from fastapi import Header, HTTPException
from jose import jwt, JWTError

import logging
logger = logging.getLogger("Thronestead.Security")

__all__ = ["verify_jwt_token", "require_user_id"]


def verify_jwt_token(
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
) -> str:
    """
    Lightweight JWT payload decoder for Supabase-issued tokens.

    - Extracts `sub` field from payload (base64-encoded).
    - Compares it to the X-User-ID header value.
    - Does NOT verify signature (handled by Supabase edge or proxy).
    
    Args:
        authorization: Bearer token from `Authorization` header
        x_user_id: User ID expected from Supabase (passed in `X-User-ID`)

    Returns:
        str: Validated UUID user ID (sub)

    Raises:
        HTTPException 401: If the token is missing, malformed, or mismatched
    """
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Missing or malformed Authorization header.")
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")

    token = authorization.split()[1]

    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    try:
        if jwt_secret:
            payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        else:
            payload_part = token.split(".")[1]
            payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_part.encode("utf-8"))
            payload = json.loads(payload_bytes)
    except JWTError:
        logger.warning("JWT signature verification failed.")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as exc:
        logger.error("Failed to decode JWT payload.")
        logger.exception(exc)
        raise HTTPException(status_code=401, detail="Invalid token payload")

    uid = payload.get("sub")
    if not uid or uid != x_user_id:
        logger.warning(f"Token subject mismatch: token.sub={uid}, header={x_user_id}")
        raise HTTPException(status_code=401, detail="Token mismatch")

    try:
        return str(UUID(uid))
    except ValueError:
        logger.warning("Invalid user ID format in token.")
        raise HTTPException(status_code=401, detail="Invalid user ID")


def require_user_id(
    x_user_id: str | None = Header(None),
    authorization: str | None = Header(None),
) -> str:
    """
    Verifies `X-User-ID` is a valid UUID. Optionally cross-checks against the JWT `sub`.

    Args:
        x_user_id: Provided user ID header
        authorization: Optional Bearer token for validation

    Returns:
        str: Validated user ID string

    Raises:
        HTTPException 401: If the ID is missing, invalid, or mismatched
    """
    if not x_user_id:
        logger.warning("Missing X-User-ID header.")
        raise HTTPException(status_code=401, detail="User ID header missing")
    try:
        x_user_id = str(UUID(x_user_id))
    except ValueError:
        logger.warning("Invalid UUID format for user ID.")
        raise HTTPException(status_code=401, detail="Invalid user ID")

    if authorization:
        verify_jwt_token(authorization=authorization, x_user_id=x_user_id)

    return x_user_id
