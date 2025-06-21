# Project Name: Thronestead©
# File Name: diplomacy_center.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.audit_service import log_alliance_activity

router = APIRouter(prefix="/api/diplomacy", tags=["diplomacy_center"])

# --------------------
# Utility
# --------------------
def get_alliance_id(db: Session, user_id: str) -> int:
    """Retrieve the alliance_id of a given user."""
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return row[0]


# --------------------
# Pydantic Payloads
# --------------------
class ProposePayload(BaseModel):
    treaty_type: str
    partner_alliance_id: int


class RespondPayload(BaseModel):
    treaty_id: int
    response_action: str


# New API payloads used by metrics/treaty endpoints
class TreatyProposal(BaseModel):
    proposer_id: int
    partner_alliance_id: int
    treaty_type: str
    notes: str | None = None
    end_date: str | None = None


class TreatyResponse(BaseModel):
    treaty_id: int
    response: str
