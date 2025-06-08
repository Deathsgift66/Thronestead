from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AllianceVault

router = APIRouter(prefix="/api/alliance-vault", tags=["alliance_vault"])


class VaultTransaction(BaseModel):
    alliance_id: int = 1
    resource: str
    amount: int


@router.get("/summary")
def summary(alliance_id: int = 1, db: Session = Depends(get_db)):
    vault = db.query(AllianceVault).filter_by(alliance_id=alliance_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    resources = [
        'wood', 'stone', 'iron_ore', 'gold', 'gems',
        'food', 'coal', 'livestock', 'clay', 'flax', 'tools',
        'wood_planks', 'refined_stone', 'iron_ingots', 'charcoal',
        'leather', 'arrows', 'swords', 'axes', 'shields', 'armour',
        'wagon', 'siege_weapons', 'jewelry', 'spear', 'horses',
        'pitchforks', 'fortification_level', 'army_count'
    ]
    totals = {r: getattr(vault, r) for r in resources}
    return {"totals": totals}


@router.get("/custom-board")
async def custom_board():
    return {"board": []}


@router.post("/deposit")
def deposit(payload: VaultTransaction, db: Session = Depends(get_db)):
    vault = db.query(AllianceVault).filter_by(alliance_id=payload.alliance_id).first()
    if not vault:
        vault = AllianceVault(alliance_id=payload.alliance_id)
        db.add(vault)
    if not hasattr(vault, payload.resource):
        raise HTTPException(status_code=400, detail="Invalid resource")
    setattr(vault, payload.resource, getattr(vault, payload.resource) + payload.amount)
    db.commit()
    return {"message": "Deposited"}


@router.post("/withdraw")
def withdraw(payload: VaultTransaction, db: Session = Depends(get_db)):
    vault = db.query(AllianceVault).filter_by(alliance_id=payload.alliance_id).first()
    if not vault or not hasattr(vault, payload.resource):
        raise HTTPException(status_code=404, detail="Resource not found")
    current = getattr(vault, payload.resource)
    if current < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient amount")
    setattr(vault, payload.resource, current - payload.amount)
    db.commit()
    return {"message": "Withdrawn"}


@router.get("/history")
async def history():
    return {"history": []}

