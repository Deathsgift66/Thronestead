import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Alliance, AllianceRole, User
from backend.routers.alliance_roles import (
    RoleDeletePayload,
    RolePayload,
    RoleUpdatePayload,
    create_role,
    delete_role,
    list_roles,
    update_role,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_leader(db):
    db.add(Alliance(alliance_id=1, name="A", leader="u1"))
    db.add(
        User(
            user_id="u1",
            username="leader",
            email="l@test.com",
            alliance_id=1,
            alliance_role="Leader",
        )
    )
    db.commit()
    return "u1"


def seed_member(db):
    db.add(Alliance(alliance_id=2, name="B", leader="u2"))
    db.add(User(user_id="u2", username="m", email="m@test.com", alliance_id=2))
    db.commit()
    return "u2"


def test_list_roles_returns_rows():
    Session = setup_db()
    db = Session()
    uid = seed_leader(db)
    db.add(
        AllianceRole(
            role_id=1,
            alliance_id=1,
            role_name="Officer",
            can_invite=True,
        )
    )
    db.commit()

    result = list_roles(user_id=uid, db=db)
    assert len(result["roles"]) == 1
    assert result["roles"][0]["role_name"] == "Officer"


def test_create_role_adds_entry():
    Session = setup_db()
    db = Session()
    uid = seed_leader(db)

    create_role(RolePayload(role_name="New"), user_id=uid, db=db)
    row = db.query(AllianceRole).filter_by(alliance_id=1).first()
    assert row and row.role_name == "New"


def test_update_role_modifies_record():
    Session = setup_db()
    db = Session()
    uid = seed_leader(db)
    db.add(AllianceRole(role_id=1, alliance_id=1, role_name="Old"))
    db.commit()

    update_role(
        RoleUpdatePayload(role_id=1, role_name="Updated", can_invite=True, can_kick=True, can_manage_resources=False),
        user_id=uid,
        db=db,
    )
    role = db.query(AllianceRole).filter_by(role_id=1).first()
    assert role.role_name == "Updated" and role.can_invite is True and role.can_kick is True


def test_delete_role_removes_record():
    Session = setup_db()
    db = Session()
    uid = seed_leader(db)
    db.add(AllianceRole(role_id=1, alliance_id=1, role_name="Temp"))
    db.commit()

    delete_role(RoleDeletePayload(role_id=1), user_id=uid, db=db)
    assert db.query(AllianceRole).filter_by(role_id=1).first() is None


def test_create_requires_leader():
    Session = setup_db()
    db = Session()
    uid = seed_member(db)
    with pytest.raises(HTTPException):
        create_role(RolePayload(role_name="X"), user_id=uid, db=db)
