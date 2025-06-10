from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, KingdomResources
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/resources", tags=["resources"])

@router.get("")
def get_resources(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return the player's kingdom resource ledger."""
    user = db.query(User).filter_by(user_id=user_id).first()
    if not user or not user.kingdom_id:
        raise HTTPException(status_code=404, detail="Kingdom not found")

    row = db.query(KingdomResources).filter_by(kingdom_id=user.kingdom_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Resources not found")

    resources = {c.name: getattr(row, c.name) for c in KingdomResources.__table__.columns}
    return {"resources": resources}
