from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import War
from ..security import verify_jwt_token
from .progression_router import get_kingdom_id
from services.audit_service import log_action

router = APIRouter(prefix="/api/wars", tags=["wars"])


class DeclarePayload(BaseModel):
    target: str


@router.post("/declare")
async def declare_war(
    payload: DeclarePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Declare a new war if the kingdom has available knights."""
    kid = get_kingdom_id(db, user_id)
    knights = db.execute(
        text("SELECT COUNT(*) FROM kingdom_knights WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]
    if knights == 0:
        raise HTTPException(status_code=403, detail="No knights available")
    log_action(db, user_id, "start_war", f"Declared war on {payload.target}")
    return {"message": "War declared", "target": payload.target}


def _serialize_war(war: War) -> dict:
    return {
        "war_id": war.war_id,
        "attacker_name": war.attacker_name,
        "defender_name": war.defender_name,
        "war_reason": war.war_reason,
        "status": war.status,
        "start_date": war.start_date,
        "end_date": war.end_date,
        "attacker_score": war.attacker_score,
        "defender_score": war.defender_score,
    }


@router.get("/list")
def list_wars(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return recent wars sorted by start date."""
    rows = (
        db.query(War)
        .order_by(War.start_date.desc())
        .limit(25)
        .all()
    )
    return {"wars": [_serialize_war(r) for r in rows]}


@router.get("/view")
def view_war(
    war_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return details for a single war."""
    war = db.query(War).filter(War.war_id == war_id).first()
    if not war:
        raise HTTPException(status_code=404, detail="War not found")
    return {"war": _serialize_war(war)}

