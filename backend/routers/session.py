from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from jose import JWTError
from sqlalchemy import text
from sqlalchemy.orm import Session
import time

from ..database import get_db
from ..security import decode_supabase_jwt

from ..supabase_client import get_supabase_client, maybe_await

router = APIRouter(prefix="/api/session", tags=["session"])

# Cache for validated session tokens
SESSION_CACHE: dict[str, tuple[str, float]] = {}


class TokenPayload(BaseModel):
    token: str


@router.post("/store")
def store_session_cookie(
    payload: TokenPayload, request: Request, response: Response
):
    """Store the session token in an HttpOnly cookie."""
    # Determine the domain from the Host header if available. Using the header
    # avoids issues where request.url.hostname may not match the browser's
    # perceived domain (e.g. when behind a proxy).  Fall back to the URL host
    # to keep backwards compatibility with tests and existing deployments.
    host = request.headers.get("host")
    domain = host.split(":", 1)[0] if host else request.url.hostname

    response.set_cookie(
        "session_token",
        payload.token,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/api",
        domain=domain,
    )
    # Cache the decoded token for fallback validation
    try:
        claims = decode_supabase_jwt(payload.token)
        uid = claims.get("sub")
        exp = claims.get("exp")
        if uid and exp:
            SESSION_CACHE[payload.token] = (str(uid), float(exp))
    except JWTError:
        pass
    return {"stored": True}


@router.get("/validate")
async def validate_session(request: Request):
    """Validate and decode the current Supabase session token."""
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    supabase = get_supabase_client()
    try:
        user = maybe_await(supabase.auth.get_user(token))
    except Exception as exc:  # pragma: no cover - network failure
        raise HTTPException(status_code=401, detail="Invalid session") from exc

    if isinstance(user, dict) and user.get("error"):
        raise HTTPException(status_code=401, detail="Invalid session")

    return user


@router.get("/fallback_validate")
def fallback_validate(
    request: Request, db: Session = Depends(get_db)
):
    """Validate the token using local decoding and cached sessions."""
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        claims = decode_supabase_jwt(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid session")

    uid = claims.get("sub")
    exp = claims.get("exp")
    now = time.time()
    if not uid or exp is None or float(exp) <= now:
        SESSION_CACHE.pop(token, None)
        raise HTTPException(status_code=401, detail="Invalid session")

    record = SESSION_CACHE.get(token)
    if record and record[0] == uid and record[1] > now:
        return {"id": uid}

    row = db.execute(
        text(
            "SELECT session_id FROM user_active_sessions WHERE user_id = :uid LIMIT 1"
        ),
        {"uid": uid},
    ).fetchone()
    user_row = db.execute(
        text(
            "SELECT user_id FROM users WHERE user_id = :uid OR auth_user_id = :uid"
        ),
        {"uid": uid},
    ).fetchone()
    if row and user_row:
        SESSION_CACHE[token] = (uid, float(exp))
        return {"id": uid}

    raise HTTPException(status_code=401, detail="Invalid session")
