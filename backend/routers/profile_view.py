from fastapi import APIRouter, Depends, HTTPException

from ..security import verify_jwt_token


def get_supabase_client():
    """Return a configured Supabase client or raise if unavailable."""
    try:  # pragma: no cover - optional dependency
        from supabase import create_client
    except ImportError as e:  # pragma: no cover - library missing
        raise RuntimeError("supabase client library not installed") from e
    import os
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Supabase credentials not configured")
    return create_client(url, key)


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
