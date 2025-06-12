from fastapi import APIRouter, Depends, HTTPException
from ..security import verify_jwt_token
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..supabase_client import get_supabase_client
from ..database import get_db
from backend.models import Notification, TradeLog


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


@router.get("/counters")
def navbar_counters(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return unread counts for messages, notifications and recent trades."""
    supabase = get_supabase_client()

    msg_res = (
        supabase.table("player_messages")
        .select("message_id")
        .eq("recipient_id", user_id)
        .eq("is_read", False)
        .execute()
    )
    unread_messages = len(getattr(msg_res, "data", msg_res) or [])

    notif_count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .filter(Notification.is_read.is_(False))
        .count()
    )

    cutoff = datetime.utcnow() - timedelta(hours=24)
    trade_count = db.query(TradeLog).filter(TradeLog.timestamp > cutoff).count()

    return {
        "unread_messages": unread_messages,
        "unread_notifications": notif_count,
        "recent_trades": trade_count,
    }
