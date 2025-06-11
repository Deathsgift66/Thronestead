from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from ..supabase_client import get_supabase_client
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/messages", tags=["messages"])


def get_current_user_id(
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
) -> str:
    """Authenticate user via JWT headers."""
    return verify_jwt_token(authorization, x_user_id)


class MessagePayload(BaseModel):
    recipient: str
    subject: str | None = None
    content: str


@router.get("/inbox")
async def list_inbox(user_id: str = Depends(verify_jwt_token)):
    supabase = get_supabase_client()
    res = (
        supabase.table("player_messages")
        .select(
            "message_id,subject,message,sent_at,is_read,user_id,users(username)"
        )
        .eq("recipient_id", user_id)
        .eq("deleted_by_recipient", False)
        .order("sent_at", desc=True)
        .limit(100)
        .execute()
    )

    messages = [
        {
            "message_id": r["message_id"],
            "subject": r["subject"],
            "message": r["message"],
            "sent_at": r["sent_at"],
            "is_read": r["is_read"],
            "sender": r.get("users", {}).get("username"),
        }
        for r in res.data or []
    ]
    return {"messages": messages}


@router.get("/view/{message_id}")
async def view_message(message_id: int, user_id: str = Depends(verify_jwt_token)):
    supabase = get_supabase_client()
    res = (
        supabase.table("player_messages")
        .select("* , users(username)")
        .eq("message_id", message_id)
        .eq("recipient_id", user_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Message not found")

    supabase.table("player_messages").update({"is_read": True}).eq(
        "message_id", message_id
    ).execute()
    row = res.data
    return {
        "message_id": row["message_id"],
        "subject": row["subject"],
        "message": row["message"],
        "sent_at": row["sent_at"],
        "is_read": True,
        "sender": row.get("users", {}).get("username"),
    }


@router.post("/delete/{message_id}")
async def delete_message_route(
    message_id: int, user_id: str = Depends(verify_jwt_token)
):
    supabase = get_supabase_client()
    res = (
        supabase.table("player_messages")
        .select("message_id")
        .eq("message_id", message_id)
        .eq("recipient_id", user_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Message not found")

    supabase.table("player_messages").update({"deleted_by_recipient": True}).eq(
        "message_id", message_id
    ).execute()
    return {"status": "deleted", "message_id": message_id}


@router.post("/send")
async def send_message(
    payload: MessagePayload, user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()
    rec = (
        supabase.table("users")
        .select("user_id")
        .eq("username", payload.recipient)
        .single()
        .execute()
    )
    if not rec.data:
        raise HTTPException(status_code=404, detail="Recipient not found")

    insert_res = (
        supabase.table("player_messages")
        .insert(
            {
                "recipient_id": rec.data["user_id"],
                "user_id": user_id,
                "subject": payload.subject,
                "message": payload.content,
            }
        )
        .execute()
    )
    mid = insert_res.data[0]["message_id"] if insert_res.data else None
    return {"message": "sent", "message_id": mid}


@router.get("/list")
async def list_messages(user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    res = (
        supabase.table("player_messages")
        .select(
            "message_id,subject,message,sent_at,is_read,user_id,users(username)"
        )
        .eq("recipient_id", user_id)
        .eq("deleted_by_recipient", False)
        .order("sent_at", desc=True)
        .execute()
    )
    messages = [
        {
            "message_id": r["message_id"],
            "subject": r["subject"],
            "message": r["message"],
            "sent_at": r["sent_at"],
            "is_read": r["is_read"],
            "user_id": r["user_id"],
            "username": r.get("users", {}).get("username"),
        }
        for r in res.data or []
    ]
    return {"messages": messages}


class DeletePayload(BaseModel):
    message_id: int


@router.post("/delete")
async def delete_message(payload: DeletePayload, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    res = (
        supabase.table("player_messages")
        .select("message_id")
        .eq("message_id", payload.message_id)
        .eq("recipient_id", user_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Message not found")
    supabase.table("player_messages").update({"deleted_by_recipient": True}).eq(
        "message_id", payload.message_id
    ).execute()
    return {"status": "deleted"}


@router.get("/{message_id}")
async def get_message(message_id: int, user_id: str = Depends(get_current_user_id)):
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
    supabase.table("player_messages").update({"is_read": True}).eq(
        "message_id", message_id
    ).execute()
    row = res.data
    return {
        "message_id": row["message_id"],
        "subject": row["subject"],
        "message": row["message"],
        "sent_at": row["sent_at"],
        "user_id": row["user_id"],
        "username": row.get("users", {}).get("username"),
    }

