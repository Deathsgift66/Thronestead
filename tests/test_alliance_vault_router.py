import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import AllianceVault, AllianceVaultTransactionLog, User
from backend.routers.alliance_vault import VaultTransaction, deposit, withdraw, summary


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db):
    uid = uuid.uuid4()
    user = User(
        user_id=uid,
        username="tester",
        display_name="Test User",
        email="t@example.com",
        password_hash="x",
    )
    db.add(user)
    db.commit()
    return str(uid)


def test_deposit_and_withdraw():
    Session = setup_db()
    db = Session()
    user_id = create_user(db)

    deposit(
        VaultTransaction(alliance_id=1, resource="wood", amount=100, user_id=user_id),
        db,
    )
    vault = db.query(AllianceVault).filter_by(alliance_id=1).first()
    assert vault.wood == 100
    tx = db.query(AllianceVaultTransactionLog).first()
    assert tx.action == "deposit" and tx.amount == 100

    withdraw(
        VaultTransaction(alliance_id=1, resource="wood", amount=40, user_id=user_id),
        db,
    )
    vault = db.query(AllianceVault).filter_by(alliance_id=1).first()
    assert vault.wood == 60
    tx2 = db.query(AllianceVaultTransactionLog).order_by(
        AllianceVaultTransactionLog.transaction_id.desc()
    ).first()
    assert tx2.action == "withdraw" and tx2.amount == 40


def test_summary_totals():
    Session = setup_db()
    db = Session()
    db.add(AllianceVault(alliance_id=2, wood=50, gold=75))
    db.commit()

    res = summary(alliance_id=2, db=db)
    assert res["totals"]["wood"] == 50
    assert res["totals"]["gold"] == 75
