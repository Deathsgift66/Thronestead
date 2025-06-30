from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/session", tags=["session"])


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
    return {"stored": True}


@router.get("/validate")
async def validate_session(request: Request):
    """Validate and decode the current Supabase session token."""
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    supabase = get_supabase_client()
    try:
        user = supabase.auth.get_user(token)
    except Exception as exc:  # pragma: no cover - network failure
        raise HTTPException(status_code=401, detail="Invalid session") from exc

    if isinstance(user, dict) and user.get("error"):
        raise HTTPException(status_code=401, detail="Invalid session")

    return user
