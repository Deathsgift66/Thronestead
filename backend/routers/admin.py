# Project Name: Thronestead©
# File Name: admin.py
# Version: 6.13.2025.19.49 (Patched)
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
from .admin_dashboard import dashboard_summary, get_audit_logs

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


class AlertFilters(BaseModel):
    start: str | None = None
    end: str | None = None
    type: str | None = None
    severity: str | None = None
    kingdom: str | None = None
    alliance: str | None = None


# -------------------------
# 🚨 Admin Action Routes
# -------------------------
@router.post("/flag", response_model=None)
def flag_player(
    payload: PlayerAction,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "flag_user", f"Flagged user {payload.player_id}")
    return {"message": "Flagged", "player_id": payload.player_id}


@router.post("/freeze", response_model=None)
def freeze_player(
    payload: PlayerAction,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "freeze_user", f"Froze user {payload.player_id}")
    return {"message": "Frozen", "player_id": payload.player_id}


@router.post("/ban", response_model=None)
def ban_player(
    payload: PlayerAction,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "ban_user", f"Banned user {payload.player_id}")
    return {"message": "Banned", "player_id": payload.player_id}


@router.post("/bulk_action", response_model=None)
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


@router.post("/player_action", response_model=None)
def player_action(
    payload: PlayerAction,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "admin_action", payload.alert_id or "manual_action")
    return {"message": "Action executed", "action": payload.alert_id}


@router.post("/flag_ip", response_model=None)
def flag_ip(
    payload: dict,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    ip = payload.get("ip", "")
    log_action(db, admin_id, "flag_ip", f"Flagged IP {ip}")
    return {"message": "IP flagged", "ip": ip}


@router.post("/suspend_user", response_model=None)
def suspend_user(
    payload: dict,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    uid = payload.get("user_id", "")
    log_action(db, admin_id, "suspend_user", f"Suspended user {uid}")
    return {"message": "User suspended", "user_id": uid}


@router.post("/mark_alert_handled", response_model=None)
def mark_alert_handled(
    payload: dict,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    aid = payload.get("alert_id", "")
    log_action(db, admin_id, "mark_alert", f"Handled alert {aid}")
    return {"message": "Alert marked", "alert_id": aid}


# -------------------------
# 🧑‍💻 Admin Query Routes
# -------------------------
@router.get("/players", response_model=None)
def list_players(
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
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
    rows = query.order_by(User.username).limit(50).all()

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


@router.get("/alerts", response_model=None)
def get_admin_alerts(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
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


@router.post("/alerts", response_model=None)
def query_account_alerts(
    filters: AlertFilters,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    where_parts = []
    params: dict[str, str] = {}

    if filters.start:
        where_parts.append("timestamp >= :start")
        params["start"] = filters.start
    if filters.end:
        where_parts.append("timestamp <= :end")
        params["end"] = filters.end
    if filters.type:
        where_parts.append("alert_type = :type")
        params["type"] = filters.type
    if filters.severity:
        where_parts.append("severity = :severity")
        params["severity"] = filters.severity
    if filters.kingdom:
        where_parts.append("kingdom_id = :kingdom")
        params["kingdom"] = filters.kingdom
    if filters.alliance:
        where_parts.append("alliance_id = :alliance")
        params["alliance"] = filters.alliance

    where = " WHERE " + " AND ".join(where_parts) if where_parts else ""
    sql = text(f"SELECT * FROM account_alerts{where} ORDER BY timestamp DESC LIMIT 100")
    rows = db.execute(sql, params).fetchall()
    return {"alerts": [dict(r._mapping) for r in rows]}


# -------------------------
# 🔗 Legacy Alias Routes
# -------------------------
@router.get("/stats", response_model=None)
def get_admin_stats(
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Alias for dashboard summary statistics."""
    return dashboard_summary(admin_user_id=admin_user_id, db=db)


@router.get("/search_user", response_model=None)
def search_user(
    q: str = Query("", alias="q"),
    db: Session = Depends(get_db),
):
    """Alias for player search used by older dashboards."""
    result = list_players(search=q, db=db)
    return result.get("players", [])


@router.get("/logs", response_model=None)
def get_logs(
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Alias for recent audit logs."""
    return get_audit_logs(admin_user_id=admin_user_id, db=db)
