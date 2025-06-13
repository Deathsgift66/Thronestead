# Project Name: Kingmakers Rise©
# File Name: player_management.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ..security import verify_jwt_token


from ..supabase_client import get_supabase_client
from services.audit_service import fetch_user_related_logs
from ..database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/admin", tags=["player_management"])


class BulkAction(BaseModel):
    action: str
    player_ids: list[str]


class PlayerAction(BaseModel):
    action: str
    player_id: str


@router.get("/players")
def players(
    search: str | None = None,
    user_id: str = Depends(verify_jwt_token),
):
    supabase = get_supabase_client()
    query = (
        supabase.table("users")
        .select("user_id,username,email,vip_tier,status")
    )
    if search:
        query = query.or_(
            f"user_id.ilike.%{search}%,username.ilike.%{search}%,email.ilike.%{search}%"
        )
    res = query.limit(100).execute()
    players = getattr(res, "data", res) or []
    # Fetch kingdom names
    for p in players:
        kid_res = (
            supabase.table("kingdoms")
            .select("kingdom_name")
            .eq("user_id", p["user_id"])
            .single()
            .execute()
        )
        p["kingdom_name"] = (getattr(kid_res, "data", kid_res) or {}).get("kingdom_name")
    return {"players": players}


@router.post("/bulk_action")
def bulk_action(
    payload: BulkAction,
    user_id: str = Depends(verify_jwt_token),
):
    supabase = get_supabase_client()
    if payload.action == "ban":
        supabase.table("users").update({"status": "banned"}).in_("user_id", payload.player_ids).execute()
    elif payload.action == "flag":
        supabase.table("users").update({"flagged": True}).in_("user_id", payload.player_ids).execute()
    elif payload.action == "logout":
        supabase.table("user_active_sessions").update({"session_status": "expired"}).in_("user_id", payload.player_ids).execute()
    elif payload.action == "reset_password":
        supabase.table("users").update({"force_password_reset": True}).in_("user_id", payload.player_ids).execute()
    else:
        raise HTTPException(status_code=400, detail="Unknown action")
    return {"message": "bulk done", "count": len(payload.player_ids)}


@router.post("/player_action")
def player_action(
    payload: PlayerAction,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    supabase = get_supabase_client()
    if payload.action == "ban":
        supabase.table("users").update({"status": "banned"}).eq("user_id", payload.player_id).execute()
    elif payload.action == "flag":
        supabase.table("users").update({"flagged": True}).eq("user_id", payload.player_id).execute()
    elif payload.action == "freeze":
        supabase.table("users").update({"status": "frozen"}).eq("user_id", payload.player_id).execute()
    elif payload.action == "history":
        logs = fetch_user_related_logs(db, payload.player_id)
        return {"history": logs}
    else:
        raise HTTPException(status_code=400, detail="Unknown action")
    return {"message": "action done", "player": payload.player_id}

