# Project Name: Kingmakers Rise©
# File Name: profile_view.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends, HTTPException

from ..security import verify_jwt_token


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/overview")
def profile_overview(user_id: str = Depends(verify_jwt_token)):
    """Return summary profile information for the given user."""
    supabase = get_supabase_client()
    try:
        user_res = (
            supabase.table("users")
            .select("username,kingdom_name,profile_bio,profile_picture_url")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        msg_res = (
            supabase.table("player_messages")
            .select("message_id")
            .eq("recipient_id", user_id)
            .eq("is_read", False)
            .execute()
        )
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="Failed to fetch profile") from exc

    user = getattr(user_res, "data", user_res)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    unread = len(getattr(msg_res, "data", msg_res) or [])
    return {"user": user, "unread_messages": unread}
