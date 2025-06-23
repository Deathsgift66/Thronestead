# Project Name: Thronestead©
# File Name: test_alliance_vault_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Alliance, AllianceVault, AllianceVaultTransactionLog, User
from backend.routers.alliance_vault import (
    VaultTransaction,
    deposit,
    summary,
    withdraw,
    custom_board,
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
