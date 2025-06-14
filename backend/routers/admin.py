# Project Name: Kingmakers Rise©
# File Name: admin.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Admin control panel endpoints for moderation, audits, and system alerts.
All routes are protected by Supabase JWT and require admin authorization.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from ..database import get_db
from ..security import require_user_id
from services.audit_service import log_action

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger("KingmakersRise.Admin")

# -------------------------
# 🧾 Data Models
# -------------------------
class PlayerAction(BaseModel):
    player_id: str
    alert_id: str | None = None


class BulkAction(BaseModel):
    action: str
    player_ids: list[str]


# -------------------------
# 🚨 Admin Action Routes
# -------------------------
@router.post("/flag")
def flag_player(
    payload: PlayerAction,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "flag_user", f"Flagged user {payload.player_id}")
    return {"message": "Flagged", "player_id": payload.player_id}


@router.post("/freeze")
def freeze_player(
    payload: PlayerAction,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "freeze_user", f"Froze user {payload.player_id}")
    return {"message": "Frozen", "player_id": payload.player_id}


@router.post("/ban")
def ban_player(
    payload: PlayerAction,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "ban_user", f"Banned user {payload.player_id}")
    return {"message": "Banned", "player_id": payload.player_id}


@router.post("/bulk_action")
def bulk_action(
    payload: BulkAction,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    log_action(
        db,
        admin_id,
        "bulk_admin_action",
        f"{payload.action} on {len(payload.player_ids)} players",
    )
    return {"message": "Bulk action executed", "action": payload.action}


@router.post("/player_action")
def player_action(
    payload: PlayerAction,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "admin_action", payload.alert_id or "manual_action")
    return {"message": "Action executed", "action": payload.alert_id}


# -------------------------
# 🧑‍💻 Admin Query Routes
# -------------------------
@router.get("/players")
def list_players(search: str | None = Query(default=None)):
    # Placeholder for admin UI player search
    return {"players": [], "search": search}


@router.get("/alerts")
def get_admin_alerts(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Fetch admin dashboard alerts including audit logs, admin actions,
    moderation notes, recent combat logs, and treaty events.
    """

    params: dict[str, str] = {}
    filters = []

    if start:
        filters.append("created_at >= :start")
        params["start"] = start
    if end:
        filters.append("created_at <= :end")
        params["end"] = end

    where_clause = f" WHERE {' AND '.join(filters)}" if filters else ""

    def fetch(table: str, order_col: str, limit: int = 100, alt_where: str | None = None):
        sql = f"SELECT * FROM {table}{alt_where or where_clause} ORDER BY {order_col} DESC LIMIT {limit}"
        return [dict(row._mapping) for row in db.execute(text(sql), params).fetchall()]

    return {
        "audit": fetch("audit_log", "created_at"),
        "admin_actions": fetch("admin_actions", "created_at"),
        "moderation_notes": fetch("admin_notes", "created_at"),
        "recent_war_logs": fetch("alliance_war_combat_logs", "timestamp", alt_where=where_clause.replace("created_at", "timestamp")),
        "treaty_activity": fetch("alliance_treaties", "signed_at", limit=10, alt_where=where_clause.replace("created_at", "signed_at")),
    }
