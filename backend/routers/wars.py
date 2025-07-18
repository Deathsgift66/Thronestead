# Project Name: Thronestead©
# File Name: wars.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: wars.py
Role: API routes for wars.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session, aliased

from backend.models import War, User
from services.audit_service import log_action
from services.vacation_mode_service import check_vacation_mode

from ..database import get_db
from ..rate_limiter import limiter
from ..security import verify_jwt_token, require_active_user_id
from .progression_router import get_kingdom_id

router = APIRouter(prefix="/api/wars", tags=["wars"])


# Payload for declaring war
class DeclarePayload(BaseModel):
    target: str
    war_reason: str | None = None


@router.post("/declare")
@limiter.limit("10/minute")
def declare_war(
    request: Request,
    payload: DeclarePayload,
    user_id: str = Depends(require_active_user_id),
    db: Session = Depends(get_db),
):
    """
    Declare a new war if the player has at least one knight.
    Vacation Mode is enforced.
    """
    kid = get_kingdom_id(db, user_id)
    try:
        # Ensure kingdom is not in vacation mode
        check_vacation_mode(db, kid)

        target_kid = get_kingdom_id(db, payload.target)
        # Ensure target kingdom is not in vacation mode
        check_vacation_mode(db, target_kid)
        banned = db.execute(
            text("SELECT is_banned FROM users WHERE user_id = :uid"),
            {"uid": payload.target},
        ).fetchone()
        if banned and banned[0]:
            raise HTTPException(status_code=403, detail="Target is banned")

        # Validate knight availability
        knights = db.execute(
            text("SELECT COUNT(*) FROM kingdom_knights WHERE kingdom_id = :kid"),
            {"kid": kid},
        ).scalar()
        if knights == 0:
            raise HTTPException(status_code=403, detail="No knights available")

        # Log declaration
        log_action(db, user_id, "start_war", f"Declared war on {payload.target}")

        attacker_name = db.execute(
            text("SELECT username FROM users WHERE user_id = :uid"),
            {"uid": user_id},
        ).fetchone()
        defender_name = db.execute(
            text("SELECT username FROM users WHERE user_id = :uid"),
            {"uid": payload.target},
        ).fetchone()

        if not defender_name:
            raise HTTPException(status_code=404, detail="Target not found")

        war = War(
            attacker_id=user_id,
            defender_id=payload.target,
            attacker_name=attacker_name[0] if attacker_name else "Unknown",
            defender_name=defender_name[0],
            war_reason=payload.war_reason,
            status="active",
            attacker_kingdom_id=kid,
            defender_kingdom_id=get_kingdom_id(db, payload.target),
            submitted_by=user_id,
        )

        db.add(war)
        db.commit()
        db.refresh(war)

        return {"message": "War declared", "war_id": war.war_id}
    except HTTPException as exc:
        log_action(db, user_id, "war_fail", exc.detail, kingdom_id=kid)
        raise
    except Exception as exc:
        log_action(db, user_id, "war_fail", str(exc), kingdom_id=kid)
        raise


# Helper function to convert a War object to dict
def _serialize_war(war: War) -> dict:
    return {
        "war_id": war.war_id,
        "attacker_name": war.attacker_name,
        "defender_name": war.defender_name,
        "war_reason": war.war_reason,
        "status": war.status,
        "start_date": war.start_date.isoformat() if war.start_date else None,
        "end_date": war.end_date.isoformat() if war.end_date else None,
        "attacker_score": war.attacker_score,
        "defender_score": war.defender_score,
    }


@router.get("/list")
def list_wars(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    List the most recent wars, sorted by start date.
    Limited to 25 entries.
    """
    Attacker = aliased(User)
    Defender = aliased(User)
    rows = (
        db.query(War)
        .join(Attacker, Attacker.user_id == War.attacker_id)
        .join(Defender, Defender.user_id == War.defender_id)
        .filter(~Attacker.is_banned, ~Defender.is_banned)
        .order_by(War.start_date.desc())
        .limit(25)
        .all()
    )
    return {"wars": [_serialize_war(w) for w in rows]}


@router.get("/view")
def view_war(
    war_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    View full details for a single war by ID.
    """
    Attacker = aliased(User)
    Defender = aliased(User)
    war = (
        db.query(War)
        .join(Attacker, Attacker.user_id == War.attacker_id)
        .join(Defender, Defender.user_id == War.defender_id)
        .filter(War.war_id == war_id, ~Attacker.is_banned, ~Defender.is_banned)
        .first()
    )
    if not war:
        raise HTTPException(status_code=404, detail="War not found")

    kid = get_kingdom_id(db, user_id)
    if war.attacker_kingdom_id != kid and war.defender_kingdom_id != kid:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"war": _serialize_war(war)}
