"""Utilities for retrieving details about the current user."""

from fastapi import APIRouter, Header, HTTPException
from jose import JWTError

from ..security import decode_supabase_jwt

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/me")
def get_me(Authorization: str = Header(...)):
    """Return the decoded Supabase JWT claims for the session user."""
    if not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid auth header")

    token = Authorization.split(" ", 1)[1]
    try:
        payload = decode_supabase_jwt(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "user_id": payload["sub"],
        "email": payload["email"],
    }

