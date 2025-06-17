# Project Name: Thronestead©
# File Name: messages.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
import re
from ..supabase_client import get_supabase_client
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/messages", tags=["messages"])


class MessagePayload(BaseModel):
    recipient: str
    content: str

    _TAG_RE = re.compile(r"<[^>]+>")

    @validator("content")
    def sanitize_content(cls, v: str) -> str:  # noqa: D401
        """Strip HTML tags and enforce length limits."""
        cleaned = cls._TAG_RE.sub("", v)
        if len(cleaned) > 5000:
            raise ValueError("Message too long")
        return cleaned.strip()


class DeletePayload(BaseModel):
    message_id: int


@router.get("/inbox")
def get_inbox(user_id: str = Depends(verify_jwt_token)):
    """
    📥 Fetch the latest 100 inbox messages for the current user.
    """
    supabase = get_supabase_client()
    res = (
        supabase.table("player_messages")
        .select("message_id,message,sent_at,is_read,user_id,users(username)")
        .eq("recipient_id", user_id)
        .order("sent_at", desc=True)
        .limit(100)
        .execute()
    )
    rows = getattr(res, "data", res) or []
    return {
        "messages": [
            {
                "message_id": r["message_id"],
                "message": r["message"],
                "sent_at": r["sent_at"],
                "is_read": r["is_read"],
                "sender": r.get("users", {}).get("username"),
            }
            for r in rows
        ]
    }


@router.get("/{message_id}")
def get_message(message_id: int, user_id: str = Depends(verify_jwt_token)):
    """
    📨 View a specific message by ID and mark it as read.
    """
    supabase = get_supabase_client()
    res = (
        supabase.table("player_messages")
        .select("*, users(username)")
        .eq("message_id", message_id)
        .eq("recipient_id", user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Message not found")

    # Mark message as read
    supabase.table("player_messages").update({"is_read": True}).eq("message_id", message_id).execute()

    r = res.data
    return {
        "message_id": r["message_id"],
        "message": r["message"],
        "sent_at": r["sent_at"],
        "is_read": True,
        "user_id": r["user_id"],
        "username": r.get("users", {}).get("username"),
    }


@router.post("/send")
def send_message(payload: MessagePayload, user_id: str = Depends(verify_jwt_token)):
    """
    ✉️ Send a message to another user.
    """
    supabase = get_supabase_client()
    res = (
        supabase.table("users")
        .select("user_id")
        .eq("username", payload.recipient)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Recipient not found")

    insert = (
        supabase.table("player_messages")
        .insert(
            {
                "recipient_id": res.data["user_id"],
                "user_id": user_id,
                "message": payload.content,
            }
        )
        .execute()
    )
    if not insert.data:
        raise HTTPException(status_code=500, detail="Message send failed")

    return {"message": "sent", "message_id": insert.data[0]["message_id"]}


@router.post("/delete")
def delete_message(payload: DeletePayload, user_id: str = Depends(verify_jwt_token)):
    """
    ❌ Soft-delete a message for the recipient.
    """
    supabase = get_supabase_client()
    verify = (
        supabase.table("player_messages")
        .select("message_id")
        .eq("message_id", payload.message_id)
        .eq("recipient_id", user_id)
        .maybe_single()
        .execute()
    )
    if not verify.data:
        raise HTTPException(status_code=404, detail="Message not found")

    supabase.table("player_messages").delete().eq("message_id", payload.message_id).execute()

    return {"status": "deleted", "message_id": payload.message_id}


@router.post("/mark_all_read")
def mark_all_messages_read(user_id: str = Depends(verify_jwt_token)):
    """
    ✅ Mark all inbox messages as read.
    """
    supabase = get_supabase_client()
    supabase.table("player_messages").update({"is_read": True}).eq("recipient_id", user_id).execute()
    return {"message": "All marked read"}

# Aliases used by internal tests
list_inbox = get_inbox
view_message = get_message
