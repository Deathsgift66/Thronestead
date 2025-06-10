from fastapi import APIRouter, Depends, HTTPException
from ..security import verify_jwt_token


def get_supabase_client():
    """Return a configured Supabase client or raise if unavailable."""
    try:
        from supabase import create_client
    except ImportError as e:  # pragma: no cover - optional
        raise RuntimeError("supabase client library not installed") from e
    import os
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase credentials not configured")
    return create_client(url, key)


router = APIRouter(prefix="/api/navbar", tags=["navbar"])


@router.get("/profile")
def navbar_profile(user_id: str = Depends(verify_jwt_token)):
    """Return navbar profile data for the current user."""
    supabase = get_supabase_client()
    user_res = (
        supabase.table("users")
        .select("username,profile_picture_url")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    result = getattr(user_res, "data", None)
    if result is None and isinstance(user_res, dict):
        result = user_res.get("data")
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    user = result

    msg_res = (
        supabase.table("player_messages")
        .select("message_id")
        .eq("recipient_id", user_id)
        .eq("is_read", False)
        .execute()
    )
    unread = len(getattr(msg_res, "data", msg_res) or [])
    return {
        "username": user.get("username"),
        "profile_picture_url": user.get("profile_picture_url"),
        "unread_messages": unread,
    }
