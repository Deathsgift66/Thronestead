from datetime import datetime, timedelta

from fastapi import APIRouter
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import AllianceVault, AllianceVaultTransactionLog, User
from services.audit_service import log_action
from services.trade_log_service import record_trade

router = APIRouter(prefix="/api/alliance-vault", tags=["alliance_vault"])
# Secondary router mirroring simplified REST style endpoints used by the
# frontend specification. These simply delegate to the existing handlers
# above so tests and legacy routes continue to work.
alt_router = APIRouter(prefix="/api/vault", tags=["alliance_vault"])


def get_current_user_id(x_user_id: str | None = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID header missing")
    return x_user_id


def get_alliance_info(user_id: str, db: Session) -> tuple[int, str]:
    """Return (alliance_id, role) for the given user or raise 403."""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=403, detail="Not in an alliance")
    return user.alliance_id, user.alliance_role or "Member"


class VaultTransaction(BaseModel):
    alliance_id: int = 1
    resource: str
    amount: int


@router.get("/summary")
def summary(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    alliance_id, _ = get_alliance_info(user_id, db)
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
def deposit(
    payload: VaultTransaction,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    alliance_id, _ = get_alliance_info(user_id, db)
    if payload.alliance_id and payload.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Cannot deposit to another alliance")
    payload.alliance_id = alliance_id

    vault = db.query(AllianceVault).filter_by(alliance_id=payload.alliance_id).first()
    if not vault:
        vault = AllianceVault(alliance_id=payload.alliance_id)
        db.add(vault)
    if not hasattr(vault, payload.resource):
        raise HTTPException(status_code=400, detail="Invalid resource")
    setattr(vault, payload.resource, getattr(vault, payload.resource) + payload.amount)
    log = AllianceVaultTransactionLog(
        alliance_id=payload.alliance_id,
        user_id=user_id,
        action='deposit',
        resource_type=payload.resource,
        amount=payload.amount,
        notes='Player deposit'
    )
    db.add(log)
    db.commit()
    record_trade(
        db,
        resource=payload.resource,
        quantity=payload.amount,
        unit_price=None,
        buyer_id=None,
        seller_id=user_id,
        buyer_alliance_id=payload.alliance_id,
        seller_alliance_id=None,
        buyer_name=None,
        seller_name=None,
        trade_type="alliance_trade",
    )
    log_action(
        db,
        user_id,
        "deposit_vault",
        f"Deposited {payload.amount} {payload.resource} into Alliance Vault ID {payload.alliance_id}",
    )
    return {"message": "Deposited"}


@router.post("/withdraw")
def withdraw(
    payload: VaultTransaction,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    alliance_id, role = get_alliance_info(user_id, db)
    if payload.alliance_id and payload.alliance_id != alliance_id:
        raise HTTPException(status_code=403, detail="Cannot withdraw from another alliance")
    if role not in {"Leader", "Co-Leader", "Officer"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    payload.alliance_id = alliance_id

    vault = db.query(AllianceVault).filter_by(alliance_id=payload.alliance_id).first()
    if not vault or not hasattr(vault, payload.resource):
        raise HTTPException(status_code=404, detail="Resource not found")
    current = getattr(vault, payload.resource)
    if current < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient amount")
    setattr(vault, payload.resource, current - payload.amount)
    log = AllianceVaultTransactionLog(
        alliance_id=payload.alliance_id,
        user_id=user_id,
        action='withdraw',
        resource_type=payload.resource,
        amount=payload.amount,
        notes='Player withdrawal'
    )
    db.add(log)
    db.commit()
    record_trade(
        db,
        resource=payload.resource,
        quantity=payload.amount,
        unit_price=None,
        buyer_id=user_id,
        seller_id=None,
        buyer_alliance_id=None,
        seller_alliance_id=payload.alliance_id,
        buyer_name=None,
        seller_name=None,
        trade_type="alliance_trade",
    )
    log_action(
        db,
        user_id,
        "withdraw_vault",
        f"Withdrew {payload.amount} {payload.resource} from Alliance Vault ID {payload.alliance_id}",
    )
    return {"message": "Withdrawn"}


@router.get("/history")
def history(
    action: str | None = None,
    page: int = 1,
    days: int | None = None,
    user_id: str = Depends(get_current_user_id),
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
    records = query.order_by(AllianceVaultTransactionLog.created_at.desc()).offset((page-1)*50).limit(50).all()
    result = []
    for t, username in records:
        result.append({
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "user_id": str(t.user_id) if t.user_id else None,
            "username": username,
            "action": t.action,
            "resource_type": t.resource_type,
            "amount": t.amount,
            "notes": t.notes,
        })
    return {"history": result}


# ---------------------------------------------------------------------------
# Alternative endpoints matching the simplified `/api/vault` schema.  These
# helpers simply call the existing logic above so the behaviour remains
# consistent while allowing the frontend to use the documented routes.

@alt_router.get("/resources")
def alt_resources(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return summary(user_id, db)


@alt_router.post("/deposit")
def alt_deposit(payload: VaultTransaction, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return deposit(payload, user_id, db)


@alt_router.post("/withdraw")
def alt_withdraw(payload: VaultTransaction, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    return withdraw(payload, user_id, db)


@alt_router.get("/transactions")
def alt_transactions(
    action: str | None = None,
    page: int = 1,
    days: int | None = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return history(action, page, days, user_id, db)


@alt_router.get("/tax-policy")
def alt_tax_policy():
    # Placeholder until tax policy tables are implemented
    return {"policy": []}


