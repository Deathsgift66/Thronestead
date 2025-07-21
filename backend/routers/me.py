"""Utilities for retrieving details about the current user."""

from fastapi import APIRouter, Header, HTTPException
from jose import JWTError

from ..security import decode_supabase_jwt, verify_jwt_token

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/me")
def get_me(Authorization: str = Header(...)):
    """Return the decoded Supabase JWT claims for the session user."""
    user_id = verify_jwt_token(authorization=Authorization)
    token = Authorization.split(" ", 1)[1]
    try:
        payload = decode_supabase_jwt(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {
        "user_id": user_id,
        "email": payload.get("email"),
    }

