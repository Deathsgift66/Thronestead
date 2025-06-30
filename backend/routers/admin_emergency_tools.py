"""Admin endpoints for emergency developer actions."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.audit_service import log_action

from ..database import get_db
from ..security import require_user_id, verify_api_key
from .admin_dashboard import verify_admin

router = APIRouter(prefix="/api/admin/emergency", tags=["admin_emergency"])


class WarTick(BaseModel):
    war_id: int


@router.post("/reprocess_tick")
def reprocess_tick(
    payload: WarTick,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Re-run a war tick for the given war."""
    verify_admin(admin_user_id, db)
    db.execute(text("SELECT reprocess_war_tick(:wid)"), {"wid": payload.war_id})
    db.commit()
    log_action(db, admin_user_id, "reprocess_tick", str(payload.war_id))
    return {"status": "reprocessed", "war_id": payload.war_id}


class KingdomPayload(BaseModel):
    kingdom_id: int


@router.post("/recalculate_resources")
def recalculate_resources(
    payload: KingdomPayload,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Recalculate resources for a kingdom."""
    verify_admin(admin_user_id, db)
    db.execute(text("SELECT recalc_resources(:kid)"), {"kid": payload.kingdom_id})
    db.commit()
    log_action(db, admin_user_id, "recalculate_resources", str(payload.kingdom_id))
    return {"status": "recalculated", "kingdom_id": payload.kingdom_id}


class QuestRollback(BaseModel):
    alliance_id: int
    quest_code: str


@router.post("/rollback_quest")
def rollback_quest(
    payload: QuestRollback,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Rollback an alliance quest."""
    verify_admin(admin_user_id, db)
    db.execute(
        text("SELECT rollback_alliance_quest(:aid, :qcode)"),
        {"aid": payload.alliance_id, "qcode": payload.quest_code},
    )
    db.commit()
    log_action(
        db,
        admin_user_id,
        "rollback_quest",
        f"{payload.alliance_id}:{payload.quest_code}",
    )
    return {"status": "rolled_back", "alliance_id": payload.alliance_id, "quest_code": payload.quest_code}


@router.get("/backups")
def list_backup_queues(
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """List available backup queues."""
    verify_admin(admin_user_id, db)
    rows = db.execute(text("SELECT queue_name FROM backup_queues ORDER BY queue_name"))
    return {"queues": [r[0] for r in rows.fetchall()]}
