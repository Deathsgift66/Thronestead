"""Admin endpoints for emergency developer actions."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.audit_service import log_action

from ..database import get_db
from ..security import (
    require_user_id,
    verify_api_key,
    verify_admin,
    require_csrf_token,
    verify_emergency_ip,
    _extract_request_meta,
)
from ..rate_limiter import limiter

router = APIRouter(prefix="/api/admin/emergency", tags=["admin_emergency"])


class WarTick(BaseModel):
    war_id: int


@router.post("/reprocess_tick")
@limiter.limit("5/minute")
def reprocess_tick(
    request: Request,
    payload: WarTick,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    _ip: None = Depends(verify_emergency_ip),
    db: Session = Depends(get_db),
):
    """Re-run a war tick for the given war."""
    verify_admin(admin_user_id, db)
    db.execute(text("SELECT reprocess_war_tick(:wid)"), {"wid": payload.war_id})
    db.commit()
    ip, device = _extract_request_meta(request)
    log_action(db, admin_user_id, "reprocess_tick", str(payload.war_id), ip, device)
    return {"status": "reprocessed", "war_id": payload.war_id}


class KingdomPayload(BaseModel):
    kingdom_id: int


@router.post("/recalculate_resources")
@limiter.limit("5/minute")
def recalculate_resources(
    request: Request,
    payload: KingdomPayload,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    _ip: None = Depends(verify_emergency_ip),
    db: Session = Depends(get_db),
):
    """Recalculate resources for a kingdom."""
    verify_admin(admin_user_id, db)
    db.execute(text("SELECT recalc_resources(:kid)"), {"kid": payload.kingdom_id})
    db.commit()
    ip, device = _extract_request_meta(request)
    log_action(
        db, admin_user_id, "recalculate_resources", str(payload.kingdom_id), ip, device
    )
    return {"status": "recalculated", "kingdom_id": payload.kingdom_id}


class QuestRollback(BaseModel):
    alliance_id: int
    quest_code: str


@router.post("/rollback_quest")
@limiter.limit("5/minute")
def rollback_quest(
    request: Request,
    payload: QuestRollback,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    _ip: None = Depends(verify_emergency_ip),
    db: Session = Depends(get_db),
):
    """Rollback an alliance quest."""
    verify_admin(admin_user_id, db)
    db.execute(
        text("SELECT rollback_alliance_quest(:aid, :qcode)"),
        {"aid": payload.alliance_id, "qcode": payload.quest_code},
    )
    db.commit()
    ip, device = _extract_request_meta(request)
    log_action(
        db,
        admin_user_id,
        "rollback_quest",
        f"{payload.alliance_id}:{payload.quest_code}",
        ip,
        device,
    )
    return {
        "status": "rolled_back",
        "alliance_id": payload.alliance_id,
        "quest_code": payload.quest_code,
    }


@router.get("/backups")
@limiter.limit("5/minute")
def list_backup_queues(
    request: Request,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    _ip: None = Depends(verify_emergency_ip),
    db: Session = Depends(get_db),
):
    """List available backup queues."""
    verify_admin(admin_user_id, db)
    ip, device = _extract_request_meta(request)
    log_action(db, admin_user_id, "list_backups", "", ip, device)
    rows = db.execute(text("SELECT queue_name FROM backup_queues ORDER BY queue_name"))
    return {"queues": [r[0] for r in rows.fetchall()]}
