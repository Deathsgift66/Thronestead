import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from backend.database import Base
from backend.models import Alliance, AlliancePolicy, User
from backend.routers.alliance_policies import (
    PolicyPayload,
    active_policies,
    activate_policy,
    deactivate_policy,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db, role="Leader"):
    uid = "00000000-0000-0000-0000-000000000001"
    db.add(Alliance(alliance_id=1, name="A", leader=uid))
    user = User(
        user_id=uid,
        username="tester",
        display_name="Tester",
        email="t@example.com",
        alliance_id=1,
        alliance_role=role,
    )
    db.add(user)
    db.commit()
    return uid


def test_active_policies_returns_only_active():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    db.add(AlliancePolicy(alliance_id=1, policy_id=1, is_active=True))
    db.add(AlliancePolicy(alliance_id=1, policy_id=2, is_active=False))
    db.commit()

    res = active_policies(user_id=uid, db=db)
    assert res["policies"] == [1]


def test_activate_policy_sets_flag():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    db.add(AlliancePolicy(alliance_id=1, policy_id=2, is_active=False))
    db.commit()

    activate_policy(PolicyPayload(policy_id=2), user_id=uid, db=db)
    row = (
        db.query(AlliancePolicy)
        .filter_by(alliance_id=1, policy_id=2)
        .first()
    )
    assert row.is_active is True


def test_deactivate_policy_sets_flag():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    db.add(AlliancePolicy(alliance_id=1, policy_id=1, is_active=True))
    db.commit()

    deactivate_policy(PolicyPayload(policy_id=1), user_id=uid, db=db)
    row = (
        db.query(AlliancePolicy)
        .filter_by(alliance_id=1, policy_id=1)
        .first()
    )
    assert row.is_active is False


def test_permission_denied_for_non_leader():
    Session = setup_db()
    db = Session()
    uid = create_user(db, role="Member")
    with pytest.raises(HTTPException):
        activate_policy(PolicyPayload(policy_id=3), user_id=uid, db=db)


