# Project Name: Thronestead©
# File Name: admin_dashboard.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Admin dashboard tools for reviewing logs, auditing kingdoms,
toggling game-wide flags, and safely managing war resolutions.
"""

from typing import Any, Optional

from ..env_utils import get_env_var

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from ..rate_limiter import limiter
from pydantic import BaseModel
from sqlalchemy import text, update
from sqlalchemy.orm import Session

from backend.models import Kingdom
from services.audit_service import log_action

from ..database import get_db
from ..security import require_user_id, verify_api_key, verify_admin, require_csrf_token

router = APIRouter(prefix="/api/admin", tags=["admin_dashboard"])


# ---------------------
# 📊 Dashboard Summary
# ---------------------
@router.get("/dashboard")
def dashboard_summary(
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)

    total_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    flagged = db.execute(text("SELECT COUNT(*) FROM admin_alerts")).scalar()
    open_wars = db.execute(
        text("SELECT COUNT(*) FROM alliance_wars WHERE war_status = 'active'")
    ).scalar()

    logs = db.execute(
        text(
            """
            SELECT log_id, user_id, action, details, created_at
            FROM audit_log ORDER BY created_at DESC LIMIT 10
        """
        )
    ).fetchall()

    return {
        "active_users": total_users,
        "flagged_users": flagged,
        "suspicious_count": flagged,
        "active_wars": open_wars,
        "recent_logs": [dict(r._mapping) for r in logs],
    }


# ---------------------
# 🔍 Audit Log Search
# ---------------------
@router.get("/audit/logs")
def get_audit_logs(
    page: int = 1,
    per_page: int = 50,
    search: str = "",
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    user_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    format: str = "json",
    verify: str = Depends(verify_api_key),
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
    if start_date:
        filters.append("created_at >= :start")
        params["start"] = start_date
    if end_date:
        filters.append("created_at <= :end")
        params["end"] = end_date

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += f" ORDER BY {sort_by} {direction}"
    query += " LIMIT :limit OFFSET :offset"
    params["limit"] = per_page
    params["offset"] = (page - 1) * per_page

    rows = db.execute(text(query), params).fetchall()
    logs = [dict(r._mapping) for r in rows]

    if format == "csv" and logs:
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(logs[0].keys()))
        writer.writeheader()
        writer.writerows(logs)
        return Response(
            output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
        )

    return logs


# ---------------------
# ⚙️ System Flag Toggle
# ---------------------
@router.post("/flags/toggle")
def toggle_flag(
    flag_key: str,
    value: bool,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)
    db.execute(
        text(
            "UPDATE system_flags SET flag_value = :val, updated_at = now() "
            "WHERE flag_key = :key"
        ),
        {"val": value, "key": flag_key},
    )
    db.commit()
    log_action(db, admin_user_id, "Toggle System Flag", f"Set {flag_key} to {value}")
    return {"status": "updated"}


@router.get("/flags")
def list_flags(
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)
    rows = db.execute(text("SELECT flag_key, flag_value FROM system_flags ORDER BY flag_key"))
    return [dict(r._mapping) for r in rows]


# ---------------------
# 🏰 Kingdom Updates
# ---------------------
@router.post("/kingdoms/update")
def update_kingdom_field(
    kingdom_id: int,
    field: str,
    value: Any,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)

    allowed_fields = {
        "castle_level",
        "prestige_score",
        "status",
        "motto",
        "ruler_name",
        "alliance_id",
        "description",
        "national_theme",
        "gold",
    }
    if field not in allowed_fields:
        raise HTTPException(
            status_code=400, detail="Field not allowed for direct update."
        )

    try:
        column = getattr(Kingdom, field)
        stmt = (
            update(Kingdom)
            .where(Kingdom.kingdom_id == kingdom_id)
            .values({column: value})
        )
        db.execute(stmt)
    except AttributeError:
        db.execute(
            text(
                f"UPDATE kingdoms SET {field} = :val WHERE kingdom_id = :kid"
            ),
            {"val": value, "kid": kingdom_id},
        )
    db.commit()
    log_action(
        db, admin_user_id, "Update Kingdom", f"{field} → {value} for {kingdom_id}"
    )
    return {"status": "updated"}


class KingdomFieldUpdate(BaseModel):
    kingdom_id: int
    field: str
    value: Any


@router.post("/kingdom/update_field")
@limiter.limit("5/minute")
def update_field(
    payload: KingdomFieldUpdate,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    """Alias for ``/kingdoms/update`` using JSON payload."""
    return update_kingdom_field(
        payload.kingdom_id,
        payload.field,
        payload.value,
        verify=verify,
        admin_user_id=admin_user_id,
        db=db,
    )


# ---------------------
# 🚩 Flagged User Review
# ---------------------
@router.get("/flagged")
def get_flagged_users(
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)
    rows = db.execute(
        text(
            "SELECT user_id, type, created_at FROM admin_alerts ORDER BY created_at DESC"
        )
    ).fetchall()
    return [dict(r._mapping) for r in rows]


# ---------------------
# ⚔️ War Admin Actions
# ---------------------
class WarAction(BaseModel):
    war_id: int


@router.post("/wars/force_end")
def force_end_war(
    payload: WarAction,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)
    db.execute(
        text(
            "UPDATE wars_tactical SET war_status = 'completed', is_concluded = TRUE, ended_at = NOW() WHERE war_id = :wid"
        ),
        {"wid": payload.war_id},
    )
    db.commit()
    log_action(db, admin_user_id, "Force End War", f"War {payload.war_id}")
    return {"status": "ended", "war_id": payload.war_id}


@router.post("/wars/rollback_tick")
def rollback_combat_tick(
    payload: WarAction,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)

    db.execute(
        text(
            "UPDATE wars_tactical SET battle_tick = battle_tick - 1 WHERE war_id = :wid AND battle_tick > 0"
        ),
        {"wid": payload.war_id},
    )
    db.execute(
        text(
            "DELETE FROM combat_logs WHERE combat_id IN (SELECT combat_id FROM combat_logs WHERE war_id = :wid ORDER BY tick_number DESC LIMIT 1)"
        ),
        {"wid": payload.war_id},
    )
    db.commit()
    log_action(db, admin_user_id, "Rollback Combat Tick", f"War {payload.war_id}")
    return {"status": "rolled_back", "war_id": payload.war_id}


# ---------------------
# 💣 Manual DB Rollback Trigger
# ---------------------
class RollbackRequest(BaseModel):
    password: str


@router.post("/rollback/database")
def rollback_database(
    payload: RollbackRequest,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
):
    verify_admin(admin_user_id, db)
    master = get_env_var("MASTER_ROLLBACK_PASSWORD")
    if not master or payload.password != master:
        raise HTTPException(status_code=403, detail="Invalid master password")
    log_action(db, admin_user_id, "Rollback Database", "Admin triggered rollback")
    return {"status": "rollback_triggered"}
