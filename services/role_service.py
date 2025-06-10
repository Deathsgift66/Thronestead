from typing import Iterable, Tuple
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session


class AllianceRole:
    LEADER = "Leader"
    OFFICER = "Officer"
    MEMBER = "Member"
    APPLICANT = "Applicant"
    BANNED = "Banned"


def get_user_alliance_role(db: Session, user_id: str) -> Tuple[int, str]:
    row = db.execute(
        text("SELECT alliance_id, alliance_role FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    aid, role = row
    return aid, role or AllianceRole.MEMBER


def require_role(db: Session, user_id: str, allowed: Iterable[str]) -> Tuple[int, str]:
    aid, role = get_user_alliance_role(db, user_id)
    if role not in allowed:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return aid, role
