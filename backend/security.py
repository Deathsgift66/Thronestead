# Project Name: Thronestead©
# File Name: security.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Handles header-based user validation using Supabase-issued JWT tokens.

Lightweight decoding for in-request matching.
Signature validation is expected to be handled by Supabase middleware/gateway.
"""

import logging
import uuid
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from jose import JWTError, jwt
from sqlalchemy import text
from sqlalchemy.orm import Session

from .env_utils import get_env_var

from .database import get_db

logger = logging.getLogger("Thronestead.Security")

# Cache environment values on import to avoid repeated lookups
SUPABASE_JWT_SECRET = get_env_var("SUPABASE_JWT_SECRET")
SUPABASE_JWT_AUD = get_env_var("SUPABASE_JWT_AUD")
API_SECRET = get_env_var("API_SECRET")

__all__ = [
    "verify_jwt_token",
    "require_user_id",
    "require_active_user_id",
    "verify_api_key",
    "get_current_user",
    "verify_admin",
    "verify_reauth_token",
    "create_reauth_token",
    "validate_reauth_token",
    "decode_supabase_jwt",
]


def _extract_request_meta(request: Request | None) -> tuple[str | None, str | None]:
    """Return client IP and device hash from a request."""
    if not request:
        return None, None

    forwarded = request.headers.get("x-forwarded-for")
    ip = forwarded.split(",", 1)[0].strip() if forwarded else None
    if not ip and request.client:
        ip = request.client.host

    return ip or None, request.headers.get("X-Device-Hash")


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


def decode_supabase_jwt(token: str) -> dict:
    """Decode a Supabase JWT with strict validation."""
    secret = SUPABASE_JWT_SECRET
    if not secret:
        raise JWTError("SUPABASE_JWT_SECRET not configured")
    audience = SUPABASE_JWT_AUD
    kwargs = {"audience": audience} if audience else {"options": {"verify_aud": False}}
    return jwt.decode(token, secret, algorithms=["HS256"], **kwargs)


def verify_jwt_token(authorization: str | None = Header(None)) -> str:
    """Validate the bearer token and return the user ID."""
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning("Missing or malformed Authorization header.")
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization[7:].strip()

    try:
        payload = decode_supabase_jwt(token)
    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    uid = payload.get("sub")
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid token")

    return uid


def require_user_id(
    x_user_id: str | None = Header(None),
    authorization: str | None = Header(None),
) -> str:
    """Validate ``X-User-ID`` and optionally ensure the token is valid."""
    if not x_user_id:
        logger.warning("Missing X-User-ID header.")
        raise HTTPException(status_code=401, detail="User ID header missing")
    try:
        x_user_id = str(UUID(x_user_id))
    except ValueError:
        logger.warning("Invalid UUID format for user ID.")
        raise HTTPException(status_code=401, detail="Invalid user ID")

    if authorization:
        verify_jwt_token(authorization=authorization)

    return x_user_id


def require_active_user_id(
    request: Request = None,
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
    db: Session = Depends(get_db),
) -> str:
    """Return the verified user ID if the account is not banned."""
    user_id = verify_jwt_token(authorization=authorization)
    banned = db.execute(
        text("SELECT is_banned FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).scalar()
    ip, device_hash = _extract_request_meta(request)
    if banned or has_active_ban(db, user_id=user_id, ip=ip, device_hash=device_hash):
        raise HTTPException(403, "You are banned from this feature.")
    return user_id


def verify_api_key(x_api_key: str = Header(...)):
    """Simple API key verification against the `API_SECRET` env variable."""
    if x_api_key != API_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")


def verify_admin(user_id: str, db: Session) -> None:
    """Raise 403 if the user is not an admin."""
    res = db.execute(
        text("SELECT is_admin FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not res or not res[0]:
        raise HTTPException(status_code=403, detail="Admin access required")


async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Return the current user's profile based on the Authorization token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.split(" ")[1]
    try:
        claims = decode_supabase_jwt(token)
    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
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


# ------------------------------------------------------------
# Re-authentication Token Handling
# ------------------------------------------------------------


def create_reauth_token(db: Session, user_id: str, ttl: int = 300) -> str:
    """Generate and persist a short-lived token for sensitive actions."""
    token = uuid.uuid4().hex
    expires = datetime.utcnow() + timedelta(seconds=ttl)
    db.execute(
        text(
            """
            INSERT INTO reauth_tokens (user_id, token, expires_at)
            VALUES (:uid, :tok, :exp)
            ON CONFLICT (user_id)
            DO UPDATE SET token = EXCLUDED.token, expires_at = EXCLUDED.expires_at,
                          created_at = now()
            """
        ),
        {"uid": user_id, "tok": token, "exp": expires},
    )
    db.commit()
    return token


def validate_reauth_token(db: Session, user_id: str, token: str) -> bool:
    """Return True if the token matches and has not expired."""
    row = db.execute(
        text(
            "SELECT expires_at FROM reauth_tokens WHERE user_id = :uid AND token = :tok"
        ),
        {"uid": user_id, "tok": token},
    ).fetchone()
    return bool(row and row[0] > datetime.utcnow())


def verify_reauth_token(
    x_reauth_token: str | None = Header(None, alias="X-Reauth-Token"),
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
    db: Session = Depends(get_db),
) -> str:
    """Validate a short-lived re-authentication token for the user."""
    user_id = verify_jwt_token(authorization=authorization)
    if not x_reauth_token or not validate_reauth_token(db, user_id, x_reauth_token):
        raise HTTPException(status_code=401, detail="Invalid re-auth token")
    return user_id
