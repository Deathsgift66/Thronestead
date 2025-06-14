# Project Name: Kingmakers Rise©
# File Name: wars.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import War
from ..security import verify_jwt_token
from .progression_router import get_kingdom_id
from services.audit_service import log_action
from services.vacation_mode_service import check_vacation_mode

router = APIRouter(prefix="/api/wars", tags=["wars"])

# Payload for declaring war
class DeclarePayload(BaseModel):
    target: str
    war_reason: str | None = None

@router.post("/declare")
def declare_war(
    payload: DeclarePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Declare a new war if the player has at least one knight.
    Vacation Mode is enforced.
    """
    kid = get_kingdom_id(db, user_id)

    # Ensure kingdom is not in vacation mode
    check_vacation_mode(db, kid)

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
        status="pending",
        attacker_kingdom_id=kid,
        defender_kingdom_id=get_kingdom_id(db, payload.target),
        submitted_by=user_id,
    )

    db.add(war)
    db.commit()
    db.refresh(war)

    return {"message": "War declared", "war_id": war.war_id}


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
    rows = (
        db.query(War)
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
    war = db.query(War).filter(War.war_id == war_id).first()
    if not war:
        raise HTTPException(status_code=404, detail="War not found")
    return {"war": _serialize_war(war)}
