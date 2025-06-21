# Project Name: Thronestead©
# File Name: admin_dashboard.py
# Version: 6.13.2025.19.49 (Patched)
# Developer: Deathsgift66

"""
Admin dashboard tools for reviewing logs, auditing kingdoms,
toggling game-wide flags, and safely managing war resolutions.
"""

import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text, update
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from backend.models import Kingdom
from services.audit_service import log_action

router = APIRouter(prefix="/api/admin", tags=["admin_dashboard"])


# ---------------------
# 🛡️ Admin Verifier
# ---------------------
def verify_admin(user_id: str, db: Session) -> None:
    """Raise 403 if the user is not an admin."""
    res = db.execute(
        text("SELECT is_admin FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not res or not res[0]:
        raise HTTPException(status_code=403, detail="Admin access required")


# ---------------------
# 📊 Dashboard Summary
# ---------------------
@router.get("/dashboard", response_model=None)
def dashboard_summary(
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)

    total_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    flagged = db.execute(text("SELECT COUNT(*) FROM account_alerts")).scalar()
    open_wars = db.execute(
        text("SELECT COUNT(*) FROM alliance_wars WHERE war_status = 'active'")
    ).scalar()

    logs = db.execute(
        text("""
            SELECT log_id, user_id, action, details, created_at
            FROM audit_log ORDER BY created_at DESC LIMIT 10
        """)
    ).fetchall()

    return {
        "total_users": total_users,
        "flagged_users": flagged,
        "open_wars": open_wars,
        "recent_logs": [dict(r._mapping) for r in logs],
    }


# ---------------------
# 🔍 Audit Log Search
# ---------------------
@router.get("/audit/logs", response_model=None)
def get_audit_logs(
    page: int = 1,
    per_page: int = 50,
    search: str = "",
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    user_id: Optional[str] = Query(None),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)

    if sort_by not in {"created_at", "action", "user_id"}:
        sort_by = "created_at"
    direction = "DESC" if sort_dir.lower() == "desc" else "ASC"

    query = "SELECT * FROM audit_log"
    params: dict[str, Any] = {}
    filters = []

    if search:
        filters.append("action ILIKE :search")
        params["search"] = f"%{search}%"
    if user_id:
        filters.append("user_id = :uid")
        params["uid"] = user_id

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += f" ORDER BY {sort_by} {direction}"
    query += " LIMIT :limit OFFSET :offset"
    params["limit"] = per_page
    params["offset"] = (page - 1) * per_page

    rows = db.execute(text(query), params).fetchall()
    return [dict(r._mapping) for r in rows]


# ---------------------
# ⚙️ System Flag Toggle
# ---------------------
@router.post("/flags/toggle", response_model=None)
def toggle_flag(
    flag_key: str,
    value: bool,
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)
    db.execute(
        text("UPDATE system_flags SET is_active = :val WHERE flag_key = :key"),
        {"val": value, "key": flag_key},
    )
    db.commit()
    log_action(db, admin_user_id, "Toggle System Flag", f"Set {flag_key} to {value}")
    return {"status": "updated"}


# ---------------------
# 🏰 Kingdom Updates
# ---------------------
@router.post("/kingdoms/update", response_model=None)
def update_kingdom_field(
    kingdom_id: int,
    field: str,
    value: Any,
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)

    allowed_fields = {
        "castle_level", "prestige_score", "status", "motto", "ruler_name",
        "alliance_id", "description", "national_theme"
    }
    if field not in allowed_fields:
        raise HTTPException(status_code=400, detail="Field not allowed for direct update.")

    column = getattr(Kingdom, field)
    stmt = (
        update(Kingdom)
        .where(Kingdom.kingdom_id == kingdom_id)
        .values({column: value})
    )
    db.execute(stmt)
    db.commit()
    log_action(db, admin_user_id, "Update Kingdom", f"{field} → {value} for {kingdom_id}")
    return {"status": "updated"}


# ---------------------
# 🚩 Flagged User Review
# ---------------------
@router.get("/flagged", response_model=None)
def get_flagged_users(
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)
    rows = db.execute(
        text("SELECT player_id, alert_type, created_at FROM account_alerts ORDER BY created_at DESC")
    ).fetchall()
    return [dict(r._mapping) for r in rows]


# ---------------------
# ⚔️ War Admin Actions
# ---------------------
class WarAction(BaseModel):
    war_id: int


@router.post("/wars/force_end", response_model=None)
def force_end_war(
    payload: WarAction,
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)
    db.execute(
        text("UPDATE wars_tactical SET war_status = 'completed', is_concluded = TRUE, ended_at = NOW() WHERE war_id = :wid"),
        {"wid": payload.war_id}
    )
    db.commit()
    log_action(db, admin_user_id, "Force End War", f"War {payload.war_id}")
    return {"status": "ended", "war_id": payload.war_id}


@router.post("/wars/rollback_tick", response_model=None)
def rollback_combat_tick(
    payload: WarAction,
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)

    db.execute(
        text("UPDATE wars_tactical SET battle_tick = battle_tick - 1 WHERE war_id = :wid AND battle_tick > 0"),
        {"wid": payload.war_id}
    )
    db.execute(
        text("DELETE FROM combat_logs WHERE combat_id IN (SELECT combat_id FROM combat_logs WHERE war_id = :wid ORDER BY tick_number DESC LIMIT 1)"),
        {"wid": payload.war_id}
    )
    db.commit()
    log_action(db, admin_user_id, "Rollback Combat Tick", f"War {payload.war_id}")
    return {"status": "rolled_back", "war_id": payload.war_id}


# ---------------------
# 💣 Manual DB Rollback Trigger
# ---------------------
class RollbackRequest(BaseModel):
    password: str


@router.post("/rollback/database", response_model=None)
def rollback_database(
    payload: RollbackRequest,
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)
    master = os.getenv("MASTER_ROLLBACK_PASSWORD")
    if not master or payload.password != master:
        raise HTTPException(status_code=403, detail="Invalid master password")
    log_action(db, admin_user_id, "Rollback Database", "Admin triggered rollback")
    return {"status": "rollback_triggered"}
