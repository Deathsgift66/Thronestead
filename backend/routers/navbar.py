# Comment
# Project Name: Thronestead©
# File Name: navbar.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: navbar.py
Role: API routes for navbar.
Version: 2025-06-21
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.models import Notification, TradeLog
from services.message_service import count_unread_messages

from ..database import get_db
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/navbar", tags=["navbar"])


@router.get("/profile")
def navbar_profile(user_id: str = Depends(verify_jwt_token)):
    """
    🎭 Return navbar profile details including username, profile image, and unread messages count.
    """
    supabase = get_supabase_client()

    # Fetch user profile data
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

    # Fetch unread messages count via service
    unread_count = count_unread_messages(supabase, user_id)

    return {
        "username": result.get("username"),
        "profile_picture_url": result.get("profile_picture_url"),
        "unread_messages": unread_count,
    }


@router.get("/counters")
def navbar_counters(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    🧮 Return navbar counters:
    - Unread player messages
    - Unread notifications (personal or global)
    - Recent trades (last 24h)
    """
    supabase = get_supabase_client()

    # Count unread messages via shared service
    unread_messages = count_unread_messages(supabase, user_id)

    # Count unread notifications (global or specific)
    unread_notifications = (
        db.query(Notification)
        .filter((Notification.user_id == user_id) | (Notification.user_id.is_(None)))
        .filter(Notification.is_read.is_(False))
        .count()
    )

    # Count trades completed in last 24 hours
    cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_trades = db.query(TradeLog).filter(TradeLog.timestamp > cutoff).count()

    return {
        "unread_messages": unread_messages,
        "unread_notifications": unread_notifications,
        "recent_trades": recent_trades,
    }
