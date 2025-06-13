from fastapi import APIRouter, Depends
try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except Exception:  # pragma: no cover
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore
from pydantic import BaseModel

from ..database import get_db
from ..security import require_user_id
from services.audit_service import log_action

router = APIRouter(prefix="/api/admin", tags=["admin"])


class PlayerAction(BaseModel):
    player_id: str
    alert_id: str | None = None


class BulkAction(BaseModel):
    action: str
    player_ids: list[str]


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


@router.get("/players")
def list_players(search: str | None = None):
    return {"players": [], "search": search}


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
    log_action(db, admin_id, "admin_action", payload.alert_id or "")
    return {"message": "Action executed", "action": payload.alert_id}


@router.get("/alerts")
def get_admin_alerts(
    start: str | None = None,
    end: str | None = None,
    admin_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Aggregate recent system alerts for the admin dashboard."""

    params: dict[str, str] = {}
    filters = []
    if start:
        filters.append("created_at >= :start")
        params["start"] = start
    if end:
        filters.append("created_at <= :end")
        params["end"] = end

    where = f" WHERE {' AND '.join(filters)}" if filters else ""

    audit = db.execute(
        text(
            "SELECT * FROM audit_log" + where + " ORDER BY created_at DESC"
        ),
        params,
    ).fetchall()

    actions = db.execute(
        text(
            "SELECT * FROM admin_actions" + where + " ORDER BY created_at DESC"
        ),
        params,
    ).fetchall()

    notes = db.execute(
        text("SELECT * FROM admin_notes" + where + " ORDER BY created_at DESC"),
        params,
    ).fetchall()

    war_where = where.replace("created_at", "timestamp")
    war_logs = db.execute(
        text(
            "SELECT * FROM alliance_war_combat_logs" +
            war_where +
            " ORDER BY timestamp DESC"
        ),
        params,
    ).fetchall()

    treaty_where = where.replace("created_at", "signed_at")
    treaties = db.execute(
        text(
            "SELECT * FROM alliance_treaties" +
            treaty_where +
            " ORDER BY signed_at DESC LIMIT 10"
        ),
        params,
    ).fetchall()

    return {
        "audit": [dict(r._mapping) for r in audit],
        "admin_actions": [dict(r._mapping) for r in actions],
        "moderation_notes": [dict(r._mapping) for r in notes],
        "recent_war_logs": [dict(r._mapping) for r in war_logs],
        "treaty_activity": [dict(r._mapping) for r in treaties],
    }

