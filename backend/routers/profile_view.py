# Project Name: Thronestead©
# File Name: profile_view.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client
from services.message_service import count_unread_messages

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/overview")
def profile_overview(user_id: str = Depends(verify_jwt_token)):
    """
    Return summary profile information and unread message count for the authenticated user.
    """
    supabase = get_supabase_client()

    try:
        # Fetch user profile info (username, kingdom, bio, avatar)
        user_response = (
            supabase.table("users")
            .select("username,kingdom_name,profile_bio,profile_picture_url")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        user_data = getattr(user_response, "data", None)
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        # Count unread messages via service
        unread_count = count_unread_messages(supabase, user_id)

    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch profile") from exc

    return {
        "user": {
            "username": user_data.get("username"),
            "kingdom_name": user_data.get("kingdom_name"),
            "profile_bio": user_data.get("profile_bio"),
            "profile_picture_url": user_data.get("profile_picture_url"),
        },
        "unread_messages": unread_count,
    }
