# Project Name: Thronestead©
# File Name: admin.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Admin control panel endpoints for moderation, audits, and system alerts.
All routes are protected by Supabase JWT and require admin authorization.
"""

import logging

import re

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models import User
from services.audit_service import log_action

from ..database import get_db
from ..security import (
    require_admin_user,
    verify_api_key,
    require_user_id,
    verify_admin,
    require_csrf_token,
    create_reauth_token,
)
from ._admin_dashboard import dashboard_summary, get_audit_logs

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger("Thronestead.Admin")

# Strict validation patterns
UUID4_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.I,
)
IP_PATTERN = re.compile(
    r"^(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}$",
)


# -------------------------
# 🧾 Data Models
# -------------------------
class PlayerAction(BaseModel):
    player_id: str = Field(..., regex=UUID4_PATTERN.pattern)
    alert_id: str | None = Field(default=None, regex=UUID4_PATTERN.pattern)


class AlertID(BaseModel):
    alert_id: str = Field(..., regex=UUID4_PATTERN.pattern)


class IPPayload(BaseModel):
    ip: str = Field(..., regex=IP_PATTERN.pattern)


class SuspendPayload(BaseModel):
    user_id: str = Field(..., regex=UUID4_PATTERN.pattern)


class BulkAction(BaseModel):
    action: str
    player_ids: list[str]

    @validator("player_ids", each_item=True)
    def _validate_ids(cls, v: str) -> str:
        if not UUID4_PATTERN.match(v):
            raise ValueError("Invalid player_id")
        return v


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
@router.post("/flag")
def flag_player(
    payload: PlayerAction,
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "flag_user", f"Flagged user {payload.player_id}")
    return {"message": "Flagged", "player_id": payload.player_id}


@router.post("/freeze")
def freeze_player(
    payload: PlayerAction,
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "freeze_user", f"Froze user {payload.player_id}")
    return {"message": "Frozen", "player_id": payload.player_id}


@router.post("/ban")
def ban_player(
    payload: PlayerAction,
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "ban_user", f"Banned user {payload.player_id}")
    db.execute(
        text(
            """
            INSERT INTO bans (user_id, ban_type, issued_by, is_active)
            VALUES (:uid, 'account', :aid, true)
            """
        ),
        {"uid": payload.player_id, "aid": admin_id},
    )
    db.commit()
    return {"message": "Banned", "player_id": payload.player_id}


@router.post("/bulk_action")
def bulk_action(
    payload: BulkAction,
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
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
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    log_action(db, admin_id, "admin_action", payload.alert_id or "manual_action")
    return {"message": "Action executed", "action": payload.alert_id}


@router.post("/flag_ip")
def flag_ip(
    payload: IPPayload,
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    ip = payload.ip
    log_action(db, admin_id, "flag_ip", f"Flagged IP {ip}")
    if ip:
        db.execute(
            text(
                """
                INSERT INTO bans (ip_address, ban_type, issued_by, is_active)
                VALUES (:ip, 'ip', :aid, true)
                """
            ),
            {"ip": ip, "aid": admin_id},
        )
        db.commit()
    return {"message": "IP flagged", "ip": ip}


@router.post("/suspend_user")
def suspend_user(
    payload: SuspendPayload,
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    uid = payload.user_id
    log_action(db, admin_id, "suspend_user", f"Suspended user {uid}")
    return {"message": "User suspended", "user_id": uid}


@router.post("/mark_alert_handled")
def mark_alert_handled(
    payload: AlertID,
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    aid = payload.alert_id
    log_action(db, admin_id, "mark_alert", f"Handled alert {aid}")
    return {"message": "Alert marked", "alert_id": aid}


@router.post("/dismiss_alert")
def dismiss_alert(
    payload: AlertID,
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    """Delete an alert after verifying admin permissions."""
    aid = payload.alert_id
    if not aid:
        raise HTTPException(status_code=400, detail="alert_id required")
    db.execute(text("DELETE FROM admin_alerts WHERE alert_id = :aid"), {"aid": aid})
    db.commit()
    log_action(db, admin_id, "dismiss_alert", f"Dismissed alert {aid}")
    return {"message": "Dismissed", "alert_id": aid}


# -------------------------
# 🧑‍💻 Admin Query Routes
# -------------------------
@router.get("/players")
def list_players(
    search: str | None = Query(default=None),
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
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
            User.username.ilike(pattern)
            | User.display_name.ilike(pattern)
            | User.email.ilike(pattern)
            | User.kingdom_name.ilike(pattern)
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


@router.get("/alerts")
def get_admin_alerts(
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
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


@router.post("/alerts")
def query_admin_alerts(
    filters: AlertFilters,
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    where_parts = []
    params: dict[str, str] = {}

    if filters.start:
        where_parts.append("created_at >= :start")
        params["start"] = filters.start
    if filters.end:
        where_parts.append("created_at <= :end")
        params["end"] = filters.end
    if filters.type:
        where_parts.append("type = :type")
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
    sql = text(f"SELECT * FROM admin_alerts{where} ORDER BY created_at DESC LIMIT 100")
    rows = db.execute(sql, params).fetchall()
    return {"alerts": [dict(r._mapping) for r in rows]}


@router.post("/alerts/connect")
def alerts_connect(
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    """Return a short-lived token for websocket authentication."""
    token = create_reauth_token(db, admin_id, ttl=60)
    return {"url": f"/api/admin/alerts/live?uid={admin_id}&token={token}"}


# -------------------------
# 🔗 Legacy Alias Routes
# -------------------------
@router.get("/stats")
def get_admin_stats(
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    """Alias for dashboard summary statistics."""
    return dashboard_summary(admin_user_id=admin_user_id, db=db)


@router.get("/search_user")
def search_user(
    q: str = Query("", alias="q"),
    verify: str = Depends(verify_api_key),
    admin_id: str = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    """Alias for player search used by older dashboards."""
    result = list_players(search=q, admin_id=admin_id, verify=verify, db=db)
    return result.get("players", [])


@router.get("/logs")
def get_logs(
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    """Alias for recent audit logs."""
    return get_audit_logs(admin_user_id=admin_user_id, db=db)


@router.get("/check-admin")
def check_admin(
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return true if the requesting user is an admin."""
    verify_admin(admin_user_id, db)
    return {"is_admin": True}
