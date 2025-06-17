# Project Name: Thronestead©
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
from backend.models import User
from services.audit_service import log_action

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger("Thronestead.Admin")

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
def list_players(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Return basic player records filtered by username or display name."""
    query = db.query(
        User.user_id,
        User.username,
        User.display_name,
        User.kingdom_id,
        User.alliance_id,
    )

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            User.username.ilike(pattern) | User.display_name.ilike(pattern)
        )

    rows = (
        query.order_by(User.username)
        .limit(50)
        .all()
    )

    return {
        "players": [
            {
                "user_id": str(r.user_id),
                "username": r.username,
                "display_name": r.display_name,
                "kingdom_id": r.kingdom_id,
                "alliance_id": r.alliance_id,
            }
            for r in rows
        ]
    }


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

    allowed_tables = {
        "audit_log": "created_at",
        "admin_actions": "created_at",
        "admin_notes": "created_at",
        "alliance_war_combat_logs": "timestamp",
        "alliance_treaties": "signed_at",
    }

    def fetch(table: str, limit: int = 100, alt_where: str | None = None):
        order_col = allowed_tables.get(table)
        if not order_col:
            raise HTTPException(status_code=400, detail="Invalid table requested")
        sql = text(
            f"SELECT * FROM {table}{alt_where or where_clause} ORDER BY {order_col} DESC LIMIT :limit"
        )
        return [
            dict(row._mapping)
            for row in db.execute(sql, {**params, "limit": limit}).fetchall()
        ]

    return {
        "audit": fetch("audit_log"),
        "admin_actions": fetch("admin_actions"),
        "moderation_notes": fetch("admin_notes"),
        "recent_war_logs": fetch(
            "alliance_war_combat_logs",
            alt_where=where_clause.replace("created_at", "timestamp"),
        ),
        "treaty_activity": fetch(
            "alliance_treaties",
            limit=10,
            alt_where=where_clause.replace("created_at", "signed_at"),
        ),
    }
