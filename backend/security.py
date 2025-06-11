import base64
import json
from uuid import UUID
from fastapi import Header, HTTPException


def verify_jwt_token(
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
) -> str:
    """Lightweight verification of Supabase JWT tokens.

    Ensures the Authorization header is present, decodes the JWT payload,
    and checks that the ``sub`` claim matches the ``X-User-ID`` header.
    This does not validate the signature but prevents token/user mismatches.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.split()[1]
    try:
        payload_part = token.split(".")[1]
        # Pad base64 string if necessary
        rem = len(payload_part) % 4
        if rem:
            payload_part += "=" * (4 - rem)
        payload_bytes = base64.urlsafe_b64decode(payload_part.encode())
        payload = json.loads(payload_bytes)
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    uid = payload.get("sub")
    if not uid or uid != x_user_id:
        raise HTTPException(status_code=401, detail="Token mismatch")
    try:
        UUID(uid)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID")
    return uid
