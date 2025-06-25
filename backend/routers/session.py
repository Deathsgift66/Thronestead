from fastapi import APIRouter, HTTPException, Request

from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/session", tags=["session"])


@router.get("/validate")
async def validate_session(request: Request):
    """Validate and decode the current Supabase session token."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")

    token = auth_header.split()[1]
    supabase = get_supabase_client()
    try:
        user = supabase.auth.get_user(token)
    except Exception as exc:  # pragma: no cover - network failure
        raise HTTPException(status_code=401, detail="Invalid session") from exc

    if isinstance(user, dict) and user.get("error"):
        raise HTTPException(status_code=401, detail="Invalid session")

    return user
