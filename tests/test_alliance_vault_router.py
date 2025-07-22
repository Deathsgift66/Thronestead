# Project Name: Thronestead©
# File Name: test_alliance_vault_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import (
    Alliance,
    AllianceVault,
    AllianceVaultTransactionLog,
    User,
    AllianceTaxPolicy,
    AllianceRole,
)
from backend.routers.alliance_vault import (
    VaultTransaction,
    deposit,
    summary,
    withdraw,
    custom_board,
    view_tax_policy,
    update_tax_policy,
    TaxPolicy,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db, alliance_id=1, role="Leader"):
    uid = uuid.uuid4()
    db.add(Alliance(alliance_id=alliance_id, name="A"))
    user = User(
        user_id=uid,
        username="tester",
        display_name="Test User",
        email="t@example.com",
        alliance_id=alliance_id,
        alliance_role=role,
    )
    db.add(user)
    db.commit()
    return str(uid)


def test_deposit_and_withdraw():
    Session = setup_db()
    db = Session()
    user_id = create_user(db)

    deposit(
        VaultTransaction(alliance_id=1, resource="wood", amount=100),
        user_id,
        db,
    )
    vault = db.query(AllianceVault).filter_by(alliance_id=1).first()
    assert vault.wood == 100
    tx = db.query(AllianceVaultTransactionLog).first()
    assert tx.action == "deposit" and tx.amount == 100

    withdraw(
        VaultTransaction(alliance_id=1, resource="wood", amount=40),
        user_id,
        db,
    )
    vault = db.query(AllianceVault).filter_by(alliance_id=1).first()
    assert vault.wood == 60
    tx2 = (
        db.query(AllianceVaultTransactionLog)
        .order_by(AllianceVaultTransactionLog.transaction_id.desc())
        .first()
    )
    assert tx2.action == "withdraw" and tx2.amount == 40


def test_summary_totals():
    Session = setup_db()
    db = Session()
    user_id = create_user(db, alliance_id=2)
    db.add(AllianceVault(alliance_id=2, wood=50, gold=75))
    db.commit()

    res = summary(user_id=user_id, db=db)
    assert res["totals"]["wood"] == 50
    assert res["totals"]["gold"] == 75


def test_withdraw_permission_denied():
    Session = setup_db()
    db = Session()
    user_id = create_user(db, role="Member")

    deposit(VaultTransaction(alliance_id=1, resource="gold", amount=10), user_id, db)
    with pytest.raises(HTTPException):
        withdraw(
            VaultTransaction(alliance_id=1, resource="gold", amount=5), user_id, db
        )


def test_custom_board_returns_alliance_banner_and_text():
    Session = setup_db()
    db = Session()
    user_id = create_user(db)
    alliance = db.query(Alliance).filter_by(alliance_id=1).first()
    alliance.banner = "img.png"
    alliance.motd = "Hello"
    db.commit()

    res = custom_board(user_id=user_id, db=db)
    assert res == {"image_url": "img.png", "custom_text": "Hello"}


def test_view_tax_policy_returns_rows():
    Session = setup_db()
    db = Session()
    user_id = create_user(db)
    db.add(
        AllianceTaxPolicy(
            alliance_id=1, resource_type="gold", tax_rate_percent=5, is_active=True
        )
    )
    db.commit()

    res = view_tax_policy(user_id=user_id, db=db)
    assert res["policy"][0]["rate"] == 5


def test_update_tax_policy_checks_permissions():
    Session = setup_db()
    db = Session()
    user_id = create_user(db, role="Member")
    with pytest.raises(HTTPException):
        update_tax_policy([TaxPolicy(resource="gold", rate=10)], user_id=user_id, db=db)


def test_update_tax_policy_with_role_permission():
    Session = setup_db()
    db = Session()
    user_id = create_user(db, role="Treasurer")
    db.add(
        AllianceRole(
            role_id=1,
            alliance_id=1,
            role_name="Treasurer",
            can_manage_taxes=True,
        )
    )
    db.commit()

    update_tax_policy([TaxPolicy(resource="gold", rate=12)], user_id=user_id, db=db)
    row = (
        db.query(AllianceTaxPolicy)
        .filter_by(alliance_id=1, resource_type="gold")
        .first()
    )
    assert row and row.tax_rate_percent == 12
