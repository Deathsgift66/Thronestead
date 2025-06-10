from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Any, Optional

from ..database import get_db
from .progression_router import get_user_id
from services.audit_service import log_action

router = APIRouter(prefix="/api/admin", tags=["admin_dashboard"])


def verify_admin(user_id: str, db: Session) -> None:
    """Raise HTTP 403 if the user is not an admin."""
    res = db.execute(
        text("SELECT is_admin FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not res or not res[0]:
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/dashboard")
def dashboard_summary(
    admin_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Return basic dashboard stats and latest logs."""
    verify_admin(admin_user_id, db)
    total_users = db.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
    flagged = db.execute(text("SELECT COUNT(*) FROM account_alerts")).fetchone()[0]
    open_wars = db.execute(
        text("SELECT COUNT(*) FROM alliance_wars WHERE status = 'active'")
    ).fetchone()[0]
    logs = db.execute(
        text(
            "SELECT log_id, user_id, action, details, created_at "
            "FROM audit_log ORDER BY created_at DESC LIMIT 10"
        )
    ).fetchall()
    return {
        "total_users": total_users,
        "flagged_users": flagged,
        "open_wars": open_wars,
        "recent_logs": [dict(r._mapping) for r in logs],
    }


@router.get("/audit/logs")
def get_audit_logs(
    page: int = 1,
    per_page: int = 50,
    search: str = "",
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    user_id: Optional[str] = Query(None),
    admin_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Return paginated audit logs with optional search and sorting."""
    verify_admin(admin_user_id, db)
    base = "SELECT * FROM audit_log"
    clauses = []
    params: dict[str, Any] = {}
    if search:
        clauses.append("action ILIKE :search")
        params["search"] = f"%{search}%"
    if user_id:
        clauses.append("user_id = :uid")
        params["uid"] = user_id
    if clauses:
        base += " WHERE " + " AND ".join(clauses)
    if sort_by not in {"created_at", "action", "user_id"}:
        sort_by = "created_at"
    direction = "DESC" if sort_dir.lower() == "desc" else "ASC"
    base += f" ORDER BY {sort_by} {direction}"
    base += " LIMIT :limit OFFSET :offset"
    params["limit"] = per_page
    params["offset"] = (page - 1) * per_page
    rows = db.execute(text(base), params).fetchall()
    return [dict(r._mapping) for r in rows]


@router.post("/flags/toggle")
def toggle_flag(
    flag_key: str,
    value: bool,
    admin_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Toggle a system flag on or off."""
    verify_admin(admin_user_id, db)
    db.execute(
        text("UPDATE system_flags SET is_active = :val WHERE flag_key = :key"),
        {"val": value, "key": flag_key},
    )
    db.commit()
    log_action(
        db,
        admin_user_id,
        "Toggle System Flag",
        f"Set {flag_key} to {value}",
    )
    return {"status": "updated"}


@router.post("/kingdoms/update")
def update_kingdom_field(
    kingdom_id: int,
    field: str,
    value: Any,
    admin_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Update an arbitrary kingdom field."""
    verify_admin(admin_user_id, db)
    query = text(f"UPDATE kingdoms SET {field} = :val WHERE kingdom_id = :kid")
    db.execute(query, {"val": value, "kid": kingdom_id})
    db.commit()
    log_action(
        db,
        admin_user_id,
        "Update Kingdom",
        f"{field} -> {value} for {kingdom_id}",
    )
    return {"status": "updated"}


@router.get("/flagged")
def get_flagged_users(
    admin_user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> list[dict]:
    """Return list of flagged users for review."""
    verify_admin(admin_user_id, db)
    rows = db.execute(
        text(
            "SELECT player_id, alert_type, created_at "
            "FROM account_alerts ORDER BY created_at DESC"
        )
    ).fetchall()
    return [dict(r._mapping) for r in rows]
