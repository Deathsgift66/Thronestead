# Project Name: Thronestead©
# File Name: player_management.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: player_management.py
Role: API routes for player management.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..supabase_client import get_supabase_client
from ..security import verify_jwt_token, verify_api_key
from ..database import get_db
from services.audit_service import fetch_user_related_logs

router = APIRouter(prefix="/api/admin", tags=["player_management"])


# -----------------------------
# Request Models
# -----------------------------


class BulkAction(BaseModel):
    action: str  # valid: ban, flag, logout, reset_password
    player_ids: list[str]


class PlayerAction(BaseModel):
    action: str  # valid: ban, flag, freeze, history
    player_id: str


# -----------------------------
# Endpoint: Get Players
# -----------------------------
@router.get("/players")
def players(
    search: str | None = None,
    verify: str = Depends(verify_api_key),
    user_id: str = Depends(verify_jwt_token),
):
    """
    Admin endpoint to fetch player list with optional search by username, email, or user_id.
    """
    supabase = get_supabase_client()

    query = supabase.table("users").select("user_id,username,email,vip_tier,status")

    # Apply search filters if provided
    if search:
        query = query.or_(
            f"user_id.ilike.%{search}%,username.ilike.%{search}%,email.ilike.%{search}%"
        )

    # Execute query and return 100 max records
    res = query.limit(100).execute()
    players = getattr(res, "data", res) or []

    # Fetch kingdom names in a single query for efficiency
    user_ids = [p["user_id"] for p in players]
    if user_ids:
        mapping_res = (
            supabase.table("kingdoms")
            .select("user_id,kingdom_name")
            .in_("user_id", user_ids)
            .execute()
        )
        rows = getattr(mapping_res, "data", mapping_res) or []
        name_map = {r["user_id"]: r.get("kingdom_name") for r in rows}
        for p in players:
            p["kingdom_name"] = name_map.get(p["user_id"])

    return {"players": players}


# -----------------------------
# Endpoint: Bulk Admin Actions
# -----------------------------
@router.post("/bulk_action")
def bulk_action(
    payload: BulkAction,
    verify: str = Depends(verify_api_key),
    user_id: str = Depends(verify_jwt_token),
):
    """
    Perform bulk administrative actions on a list of players.
    Supported actions: ban, flag, logout, reset_password
    """
    supabase = get_supabase_client()
    ids = payload.player_ids

    if not ids:
        raise HTTPException(status_code=400, detail="No player IDs provided")

    if payload.action == "ban":
        supabase.table("users").update({"status": "banned"}).in_(
            "user_id", ids
        ).execute()
    elif payload.action == "flag":
        supabase.table("users").update({"flagged": True}).in_("user_id", ids).execute()
    elif payload.action == "logout":
        supabase.table("user_active_sessions").update(
            {"session_status": "expired"}
        ).in_("user_id", ids).execute()
    elif payload.action == "reset_password":
        supabase.table("users").update({"force_password_reset": True}).in_(
            "user_id", ids
        ).execute()
    else:
        raise HTTPException(status_code=400, detail="Unknown action")

    return {"message": "bulk done", "count": len(ids)}


# -----------------------------
# Endpoint: Single Player Action
# -----------------------------
@router.post("/player_action")
def player_action(
    payload: PlayerAction,
    verify: str = Depends(verify_api_key),
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Perform an administrative action on a specific player.
    Supported actions: ban, flag, freeze, history
    """
    supabase = get_supabase_client()
    pid = payload.player_id

    if payload.action == "ban":
        supabase.table("users").update({"status": "banned"}).eq(
            "user_id", pid
        ).execute()
    elif payload.action == "flag":
        supabase.table("users").update({"flagged": True}).eq("user_id", pid).execute()
    elif payload.action == "freeze":
        supabase.table("users").update({"status": "frozen"}).eq(
            "user_id", pid
        ).execute()
    elif payload.action == "history":
        logs = fetch_user_related_logs(db, pid)
        return {"history": logs}
    else:
        raise HTTPException(status_code=400, detail="Unknown action")

    return {"message": "action done", "player": pid}
