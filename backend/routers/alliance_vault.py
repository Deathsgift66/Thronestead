# Project Name: Thronestead©
# File Name: alliance_vault.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: alliance_vault.py
Role: API routes for alliance vault.
Version: 2025-06-21
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.models import (
    Alliance,
    AllianceVault,
    AllianceVaultTransactionLog,
    User,
    AllianceTaxPolicy,
    AllianceRole,
)
from services.audit_service import log_action

from ..database import get_db
from ..security import require_user_id
from ..router_utils import mirror_router

router = APIRouter(prefix="/api/alliance-vault", tags=["alliance_vault"])
alt_router = mirror_router(router, prefix="/api/vault")
custom_router = APIRouter(prefix="/api/alliance/custom", tags=["alliance_vault"])


VAULT_RESOURCES = [
    "wood",
    "stone",
    "iron_ore",
    "gold",
    "gems",
    "food",
    "coal",
    "livestock",
    "clay",
    "flax",
    "tools",
    "wood_planks",
    "refined_stone",
    "iron_ingots",
    "charcoal",
    "leather",
    "arrows",
    "swords",
    "axes",
    "shields",
    "armor",
    "wagon",
    "siege_weapons",
    "jewelry",
    "spear",
    "horses",
    "pitchforks",
    "fortification_level",
    "army_count",
]


class VaultTransaction(BaseModel):
    alliance_id: int = 1
    resource: str
    amount: int


class TaxPolicy(BaseModel):
    resource: str
    rate: float  # 0.0 to 1.0


def _has_tax_permission(db: Session, alliance_id: int, role: str) -> bool:
    """Return True if the role can manage taxes."""
    if role in {"Leader", "Co-Leader"}:
        return True
    row = (
        db.query(AllianceRole)
        .filter_by(alliance_id=alliance_id, role_name=role)
        .first()
    )
    return bool(row and (row.can_manage_taxes or row.can_manage_resources))


def get_alliance_info(user_id: str, db: Session) -> tuple[int, str]:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=403, detail="Not in an alliance")
    return user.alliance_id, user.alliance_role or "Member"


@router.get("/summary")
def get_vault_summary(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    alliance_id, _ = get_alliance_info(user_id, db)
    vault = db.query(AllianceVault).filter_by(alliance_id=alliance_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    return {"totals": {r: getattr(vault, r, 0) for r in VAULT_RESOURCES}}


@router.post("/deposit")
def deposit_resource(
    payload: VaultTransaction,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    alliance_id, _ = get_alliance_info(user_id, db)
    if payload.resource not in VAULT_RESOURCES:
        raise HTTPException(status_code=400, detail="Invalid resource type")

    vault = db.query(AllianceVault).filter_by(alliance_id=alliance_id).first()
    if not vault:
        vault = AllianceVault(alliance_id=alliance_id)
        db.add(vault)

    setattr(
        vault, payload.resource, getattr(vault, payload.resource, 0) + payload.amount
    )
    db.add(
        AllianceVaultTransactionLog(
            alliance_id=alliance_id,
            user_id=user_id,
            action="deposit",
            resource_type=payload.resource,
            amount=payload.amount,
            notes="Player deposit",
        )
    )
    db.commit()
    log_action(
        db, user_id, "deposit_vault", f"Deposited {payload.amount} {payload.resource}"
    )
    return {"message": "Deposited"}


@router.post("/withdraw")
def withdraw_resource(
    payload: VaultTransaction,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    alliance_id, role = get_alliance_info(user_id, db)
    if role not in {"Leader", "Co-Leader", "Officer"}:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if payload.resource not in VAULT_RESOURCES:
        raise HTTPException(status_code=400, detail="Invalid resource type")

    vault = db.query(AllianceVault).filter_by(alliance_id=alliance_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    current = getattr(vault, payload.resource, 0)
    if current < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient amount in vault")

    setattr(vault, payload.resource, current - payload.amount)
    db.add(
        AllianceVaultTransactionLog(
            alliance_id=alliance_id,
            user_id=user_id,
            action="withdraw",
            resource_type=payload.resource,
            amount=payload.amount,
            notes="Player withdrawal",
        )
    )
    db.commit()
    log_action(
        db, user_id, "withdraw_vault", f"Withdrew {payload.amount} {payload.resource}"
    )
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
    records = (
        query.order_by(AllianceVaultTransactionLog.created_at.desc())
        .offset((page - 1) * 50)
        .limit(50)
        .all()
    )
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


@router.get("/interest")
def calculate_interest(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    alliance_id, _ = get_alliance_info(user_id, db)
    vault = db.query(AllianceVault).filter_by(alliance_id=alliance_id).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    interest_rate = 0.01  # 1% hourly simple interest
    return {
        "interest": {
            r: round(getattr(vault, r, 0) * interest_rate, 2) for r in VAULT_RESOURCES
        }
    }


@router.get("/tax-policy")
def view_tax_policy(
    user_id: str = Depends(require_user_id), db: Session = Depends(get_db)
):
    alliance_id, _ = get_alliance_info(user_id, db)
    rows = (
        db.query(AllianceTaxPolicy)
        .filter_by(alliance_id=alliance_id, is_active=True)
        .order_by(AllianceTaxPolicy.resource_type)
        .all()
    )
    return {
        "policy": [
            {"resource": r.resource_type, "rate": float(r.tax_rate_percent)}
            for r in rows
        ]
    }


@router.post("/tax-policy")
def update_tax_policy(
    policies: list[TaxPolicy],
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    alliance_id, role = get_alliance_info(user_id, db)
    if not _has_tax_permission(db, alliance_id, role):
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    for p in policies:
        row = (
            db.query(AllianceTaxPolicy)
            .filter_by(alliance_id=alliance_id, resource_type=p.resource)
            .first()
        )
        if row:
            row.tax_rate_percent = p.rate
            row.updated_by = user_id
            row.is_active = True
        else:
            db.add(
                AllianceTaxPolicy(
                    alliance_id=alliance_id,
                    resource_type=p.resource,
                    tax_rate_percent=p.rate,
                    updated_by=user_id,
                    is_active=True,
                )
            )
    db.commit()
    return {"message": "Updated", "policies": [p.dict() for p in policies]}


@router.get("/custom-board")
def custom_board(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return the alliance banner image and message of the day."""
    alliance_id, _ = get_alliance_info(user_id, db)
    alliance = db.query(Alliance).filter(Alliance.alliance_id == alliance_id).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return {"image_url": alliance.banner, "custom_text": alliance.motd}


# Mirror all routes under the alternate prefixes via ``mirror_router``
custom_router.include_router(router)

# Additional custom endpoint
custom_router.get("/vault")(custom_board)

