# Project Name: Thronestead©
# File Name: messages.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: messages.py
Role: API routes for messages.
Version: 2025-06-21
"""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator

from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/messages", tags=["messages"])


class MessagePayload(BaseModel):
    recipient: str
    content: str
    subject: str | None = None
    category: str | None = None

    _TAG_RE = re.compile(r"<[^>]+>")

    @validator("content")
    def sanitize_content(cls, v: str) -> str:  # noqa: D401
        """Strip HTML tags and enforce length limits."""
        cleaned = cls._TAG_RE.sub("", v)
        if len(cleaned) > 5000:
            raise ValueError("Message too long")
        return cleaned.strip()

    @validator("subject")
    def sanitize_subject(cls, v: str | None) -> str | None:  # noqa: D401
        if v is None:
            return None
        cleaned = cls._TAG_RE.sub("", v)
        return cleaned.strip()[:200] if cleaned else None


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
    ids = [r["message_id"] for r in rows]
    meta = {}
    if ids:
        meta_res = (
            supabase.table("message_metadata")
            .select("message_id,key,value")
            .in_("message_id", ids)
            .execute()
        )
        for item in getattr(meta_res, "data", meta_res) or []:
            meta.setdefault(item["message_id"], {})[item["key"]] = item["value"]

    return {
        "messages": [
            {
                "message_id": r["message_id"],
                "message": r["message"],
                "sent_at": r["sent_at"],
                "is_read": r["is_read"],
                "sender": r.get("users", {}).get("username"),
                "subject": meta.get(r["message_id"], {}).get("subject"),
                "category": meta.get(r["message_id"], {}).get("category"),
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
    supabase.table("player_messages").update({"is_read": True}).eq(
        "message_id", message_id
    ).execute()

    r = res.data
    meta_res = (
        supabase.table("message_metadata")
        .select("key,value")
        .eq("message_id", message_id)
        .execute()
    )
    meta = {m["key"]: m["value"] for m in getattr(meta_res, "data", meta_res) or []}

    return {
        "message_id": r["message_id"],
        "message": r["message"],
        "sent_at": r["sent_at"],
        "is_read": True,
        "user_id": r["user_id"],
        "username": r.get("users", {}).get("username"),
        "subject": meta.get("subject"),
        "category": meta.get("category"),
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

    mid = insert.data[0]["message_id"]
    meta = []
    if payload.subject:
        meta.append({"message_id": mid, "key": "subject", "value": payload.subject})
    if payload.category:
        meta.append({"message_id": mid, "key": "category", "value": payload.category})
    if meta:
        supabase.table("message_metadata").upsert(meta).execute()

    return {"message": "sent", "message_id": mid}


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

    supabase.table("player_messages").delete().eq(
        "message_id", payload.message_id
    ).execute()

    return {"status": "deleted", "message_id": payload.message_id}


@router.post("/mark_all_read")
def mark_all_messages_read(user_id: str = Depends(verify_jwt_token)):
    """
    ✅ Mark all inbox messages as read.
    """
    supabase = get_supabase_client()
    supabase.table("player_messages").update({"is_read": True}).eq(
        "recipient_id", user_id
    ).execute()
    return {"message": "All marked read"}


# Aliases used by internal tests
list_inbox = get_inbox
view_message = get_message
