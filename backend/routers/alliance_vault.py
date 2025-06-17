# Project Name: Thronestead©
# File Name: alliance_vault.py
# Version: 6.13.2025.21.00
# Developer: Deathsgift66

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import AllianceVault, AllianceVaultTransactionLog, User
from services.audit_service import log_action
from ..security import require_user_id

# Primary and alternative API routes
router = APIRouter(prefix="/api/alliance-vault", tags=["alliance_vault"])
alt_router = APIRouter(prefix="/api/vault", tags=["alliance_vault"])

# Define valid resources handled by the vault
VAULT_RESOURCES = [
    'wood', 'stone', 'iron_ore', 'gold', 'gems', 'food', 'coal', 'livestock',
    'clay', 'flax', 'tools', 'wood_planks', 'refined_stone', 'iron_ingots',
    'charcoal', 'leather', 'arrows', 'swords', 'axes', 'shields', 'armour',
    'wagon', 'siege_weapons', 'jewelry', 'spear', 'horses', 'pitchforks',
    'fortification_level', 'army_count'
]

class VaultTransaction(BaseModel):
    alliance_id: int = 1
    resource: str
    amount: int

def get_alliance_info(user_id: str, db: Session) -> tuple[int, str]:
    """Returns the alliance ID and role of the user."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=403, detail="Not in an alliance")
    return user.alliance_id, user.alliance_role or "Member"

@router.get("/summary")
def get_vault_summary(user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    alliance_id, _ = get_alliance_info(user_id, db)
    vault = db.query(AllianceVault).filter_by(alliance_id=alliance_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    return {"totals": {r: getattr(vault, r, 0) for r in VAULT_RESOURCES}}

@router.post("/deposit")
def deposit_resource(payload: VaultTransaction, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    alliance_id, _ = get_alliance_info(user_id, db)
    if payload.alliance_id and payload.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Cannot deposit to another alliance")
    payload.alliance_id = alliance_id

    if payload.resource not in VAULT_RESOURCES:
        raise HTTPException(status_code=400, detail="Invalid resource type")

    vault = db.query(AllianceVault).filter_by(alliance_id=alliance_id).first()
    if not vault:
        vault = AllianceVault(alliance_id=alliance_id)
        db.add(vault)

    setattr(vault, payload.resource, getattr(vault, payload.resource, 0) + payload.amount)

    db.add(AllianceVaultTransactionLog(
        alliance_id=alliance_id,
        user_id=user_id,
        action='deposit',
        resource_type=payload.resource,
        amount=payload.amount,
        notes='Player deposit'
    ))
    db.commit()

    log_action(db, user_id, "deposit_vault", f"Deposited {payload.amount} {payload.resource}")
    return {"message": "Deposited"}

@router.post("/withdraw")
def withdraw_resource(payload: VaultTransaction, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    alliance_id, role = get_alliance_info(user_id, db)
    if payload.alliance_id and payload.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Cannot withdraw from another alliance")
    if role not in {"Leader", "Co-Leader", "Officer"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    payload.alliance_id = alliance_id

    if payload.resource not in VAULT_RESOURCES:
        raise HTTPException(status_code=400, detail="Invalid resource type")

    vault = db.query(AllianceVault).filter_by(alliance_id=alliance_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    current = getattr(vault, payload.resource, 0)
    if current < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient amount in vault")

    setattr(vault, payload.resource, current - payload.amount)

    db.add(AllianceVaultTransactionLog(
        alliance_id=alliance_id,
        user_id=user_id,
        action='withdraw',
        resource_type=payload.resource,
        amount=payload.amount,
        notes='Player withdrawal'
    ))
    db.commit()

    log_action(db, user_id, "withdraw_vault", f"Withdrew {payload.amount} {payload.resource}")
    return {"message": "Withdrawn"}

@router.get("/history")
def get_transaction_history(
    action: str | None = None,
    page: int = 1,
    days: int | None = None,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    alliance_id, _ = get_alliance_info(user_id, db)
    query = (
        db.query(AllianceVaultTransactionLog, User.username)
        .join(User, AllianceVaultTransactionLog.user_id == User.user_id, isouter=True)
        .filter(AllianceVaultTransactionLog.alliance_id == alliance_id)
    )
    if action:
        query = query.filter(AllianceVaultTransactionLog.action == action)
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(AllianceVaultTransactionLog.created_at >= cutoff)

    records = query.order_by(AllianceVaultTransactionLog.created_at.desc()).offset((page - 1) * 50).limit(50).all()

    return {
        "history": [
            {
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "user_id": str(t.user_id),
                "username": username,
                "action": t.action,
                "resource_type": t.resource_type,
                "amount": t.amount,
                "notes": t.notes,
            }
            for t, username in records
        ]
    }

# Simplified mirror endpoints for legacy routes or cleaner frontend access
@alt_router.get("/resources")
def alt_summary(user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    return get_vault_summary(user_id, db)

@alt_router.post("/deposit")
def alt_deposit(payload: VaultTransaction, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    return deposit_resource(payload, user_id, db)

@alt_router.post("/withdraw")
def alt_withdraw(payload: VaultTransaction, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    return withdraw_resource(payload, user_id, db)

@alt_router.get("/transactions")
def alt_transactions(action: str | None = None, page: int = 1, days: int | None = None, user_id: str = Depends(require_user_id), db: Session = Depends(get_db)):
    return get_transaction_history(action, page, days, user_id, db)

@alt_router.get("/tax-policy")
def alt_tax_policy():
    return {"policy": []}  # Placeholder for future tax system
