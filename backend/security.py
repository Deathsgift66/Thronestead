# Project Name: Thronestead©
# File Name: security.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Handles header-based user validation using Supabase-issued JWT tokens.

Lightweight decoding for in-request matching.
Signature validation is expected to be handled by Supabase middleware/gateway.
"""

import logging
import os
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

from .database import get_db

logger = logging.getLogger("Thronestead.Security")

__all__ = [
    "verify_jwt_token",
    "require_user_id",
    "require_active_user_id",
    "verify_api_key",
    "get_current_user",
    "validate_reauth_token",
]


def has_active_ban(
    db: Session,
    user_id: str | None = None,
    ip: str | None = None,
    device_hash: str | None = None,
) -> bool:
    """Return True if an active ban matches the given identifiers."""
    conditions = []
    params: dict[str, str] = {}
    if user_id:
        conditions.append("user_id = :uid")
        params["uid"] = user_id
    if ip:
        conditions.append("ip_address = :ip")
        params["ip"] = ip
    if device_hash:
        conditions.append("device_hash = :dev")
        params["dev"] = device_hash
    if not conditions:
        return False
    query = (
        "SELECT 1 FROM bans "
        "WHERE is_active AND (expires_at IS NULL OR expires_at > now()) AND ("
        + " OR ".join(conditions)
        + ") LIMIT 1"
    )
    return db.execute(text(query), params).fetchone() is not None


def verify_jwt_token(
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
) -> str:
    """Validate a Supabase-issued JWT token and return the matching user ID.

    - Extracts the ``sub`` claim from the payload.
    - Compares it to the ``X-User-ID`` header value.
    - Raises ``HTTPException`` if the token or header are invalid.

    Args:
        authorization: Bearer token from `Authorization` header
        x_user_id: User ID expected from Supabase (passed in `X-User-ID`)

    Returns:
        str: Validated UUID user ID (sub)

    Raises:
        HTTPException 401: If the token is missing, malformed, or mismatched
    """
    auth_header = authorization
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning("Missing or malformed Authorization header.")
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.split(" ")[1]

    jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        logger.warning("JWT signature verification failed.")
        raise HTTPException(status_code=401, detail="Invalid token")

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


def require_active_user_id(
    request: Request | None = None,
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
    db: Session = Depends(get_db),
) -> str:
    """Return the verified user ID if the account is not banned."""
    user_id = verify_jwt_token(authorization=authorization, x_user_id=x_user_id)
    banned = db.execute(
        text("SELECT is_banned FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar()
    ip = None
    device_hash = None
    if request is not None:
        ip = request.headers.get("x-forwarded-for")
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        if not ip and request.client:
            ip = request.client.host
        device_hash = request.headers.get("X-Device-Hash")
    if banned or has_active_ban(db, user_id=user_id, ip=ip, device_hash=device_hash):
        raise HTTPException(403, "You are banned from this feature.")
    return user_id


def verify_api_key(x_api_key: str = Header(...)):
    """Simple API key verification against the `API_SECRET` env variable."""
    if x_api_key != os.getenv("API_SECRET"):
        raise HTTPException(status_code=401, detail="Unauthorized")


async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Return the current user's profile based on the Authorization token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.split(" ")[1]
    secret = os.getenv("SUPABASE_JWT_SECRET")
    try:
        claims = jwt.decode(token, secret, algorithms=["HS256"])
    except JWTError:
        logger.warning("JWT signature verification failed.")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as exc:  # pragma: no cover - generic decode failures
        logger.exception("Failed to decode JWT token")
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    row = db.execute(
        text(
            "SELECT user_id, username, kingdom_id, alliance_id, setup_complete "
            "FROM users WHERE user_id = :uid"
        ),
        {"uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {
        "user_id": str(row[0]),
        "username": row[1],
        "kingdom_id": row[2],
        "alliance_id": row[3],
        "setup_complete": bool(row[4]),
    }


def validate_reauth_token(token: str, db: Session) -> str:
    """Return the user ID for a valid re-auth token."""
    db.execute(
        text("DELETE FROM reauth_tokens WHERE expires_at < :now"),
        {"now": datetime.utcnow()},
    )
    row = db.execute(
        text("SELECT user_id, expires_at FROM reauth_tokens WHERE token = :tok"),
        {"tok": token},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Re-authentication required")
    user_id, expires_at = row
    exp = expires_at
    if isinstance(exp, str):
        exp = datetime.fromisoformat(exp)
    if exp <= datetime.utcnow():
        db.execute(text("DELETE FROM reauth_tokens WHERE token = :tok"), {"tok": token})
        db.commit()
        raise HTTPException(status_code=401, detail="Re-authentication required")
    return str(user_id)
