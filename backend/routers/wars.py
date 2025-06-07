from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id

router = APIRouter(prefix="/api/wars", tags=["wars"])


class DeclarePayload(BaseModel):
    target: str


@router.post("/declare")
async def declare_war(
    payload: DeclarePayload,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    knights = db.execute(
        text("SELECT COUNT(*) FROM kingdom_knights WHERE kingdom_id = :kid"),
        {"kid": kid},
    ).fetchone()[0]
    if knights == 0:
        raise HTTPException(status_code=403, detail="No knights available")
    return {"message": "War declared", "target": payload.target}

