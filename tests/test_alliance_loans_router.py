from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Alliance, AllianceLoan, AllianceLoanRepayment, User
from backend.routers.alliance_loans import (
    LoanCreatePayload,
    RepayPayload,
    create_alliance_loan,
    list_alliance_loans,
    repay_loan,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_leader(db):
    uid = "00000000-0000-0000-0000-000000000001"
    db.add(Alliance(alliance_id=1, name="A", leader=uid))
    user = User(
        user_id=uid,
        username="leader",
        email="l@test.com",
        alliance_id=1,
        alliance_role="Leader",
    )
    db.add(user)
    db.commit()
    return uid


def test_create_loan_and_list():
    Session = setup_db()
    db = Session()
    uid = seed_leader(db)
    payload = LoanCreatePayload(
        borrower_user_id=uid,
        resource_type="gold",
        amount=100,
        interest_rate=0.1,
        due_date=datetime.utcnow() + timedelta(days=7),
        schedule=[
            {
                "due_date": datetime.utcnow() + timedelta(days=7),
                "amount": 50,
            },
            {
                "due_date": datetime.utcnow() + timedelta(days=14),
                "amount": 50,
            },
        ],
    )
    create_alliance_loan(payload, uid, db)
    loans = list_alliance_loans(uid, db)
    assert len(loans["loans"]) == 1
    assert len(loans["loans"][0]["repayments"]) == 2


def test_repay_updates_schedule_and_loan():
    Session = setup_db()
    db = Session()
    uid = seed_leader(db)
    loan = AllianceLoan(
        loan_id=1,
        alliance_id=1,
        borrower_user_id=uid,
        resource_type="gold",
        amount=100,
    )
    db.add(loan)
    repay = AllianceLoanRepayment(
        schedule_id=1,
        loan_id=1,
        due_date=datetime.utcnow(),
        amount_due=50,
    )
    db.add(repay)
    db.commit()

    repay_loan(RepayPayload(schedule_id=1, amount=25), uid, db)
    db.refresh(repay)
    db.refresh(loan)
    assert repay.amount_paid == 25
    assert loan.amount_repaid == 25
