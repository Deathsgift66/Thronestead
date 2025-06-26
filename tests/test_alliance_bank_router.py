import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Alliance, AllianceGrant, User
from backend.routers.alliance_bank import GrantPayload, create_grant, list_grants


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db, alliance_id=1, role="Leader"):
    uid = str(uuid.uuid4())
    db.add(Alliance(alliance_id=alliance_id, name="A"))
    user = User(
        user_id=uid,
        username="tester",
        display_name="Test",
        email="t@example.com",
        alliance_id=alliance_id,
        alliance_role=role,
    )
    db.add(user)
    db.commit()
    return uid


def test_create_grant_records_row():
    Session = setup_db()
    db = Session()
    leader_id = create_user(db)

    create_grant(
        GrantPayload(
            recipient_user_id=leader_id,
            resource_type="gold",
            amount=50,
        ),
        leader_id,
        db,
    )

    grant = db.query(AllianceGrant).first()
    assert grant and grant.amount == 50 and grant.resource_type == "gold"


def test_list_grants_returns_created_grant():
    Session = setup_db()
    db = Session()
    leader_id = create_user(db)

    create_grant(
        GrantPayload(recipient_user_id=leader_id, resource_type="wood", amount=10),
        leader_id,
        db,
    )
    res = list_grants(user_id=leader_id, db=db)
    assert len(res["grants"]) == 1
    assert res["grants"][0]["amount"] == 10


def test_create_grant_permission_denied():
    Session = setup_db()
    db = Session()
    create_user(db)  # leader for alliance
    member_id = create_user(db, role="Member")
    with pytest.raises(HTTPException):
        create_grant(
            GrantPayload(recipient_user_id=member_id, resource_type="gold", amount=5),
            member_id,
            db,
        )
