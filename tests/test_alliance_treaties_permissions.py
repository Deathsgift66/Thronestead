from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Alliance, AllianceMember, AllianceRole, User
from backend.routers.alliance_treaties_router import ProposePayload, propose_treaty


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_alliance(db, aid):
    db.add(Alliance(alliance_id=aid, name=f"A{aid}", status="active"))
    db.commit()


def seed_member(db, aid, uid, role_name, perms):
    role_id = aid
    db.add(AllianceRole(role_id=role_id, alliance_id=aid, role_name=role_name, permissions=perms))
    db.add(User(user_id=uid, username="U", email="u@test.com", alliance_id=aid))
    db.add(AllianceMember(alliance_id=aid, user_id=uid, username="U", role_id=role_id))
    db.commit()


def test_propose_requires_leader_or_elder():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    seed_member(db, 1, "u1", "Member", ["can_manage_treaties"])
    try:
        propose_treaty(ProposePayload(treaty_type="trade_pact", partner_alliance_id=2), user_id="u1", db=db)
    except HTTPException as e:
        assert e.status_code == 403
    else:
        assert False


def test_propose_partner_must_exist():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_member(db, 1, "u1", "Leader", ["can_manage_treaties"])
    try:
        propose_treaty(ProposePayload(treaty_type="trade_pact", partner_alliance_id=99), user_id="u1", db=db)
    except HTTPException as e:
        assert e.status_code == 404
    else:
        assert False


def test_propose_inserts_record():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    seed_member(db, 1, "u1", "Leader", ["can_manage_treaties"])
    res = propose_treaty(ProposePayload(treaty_type="trade_pact", partner_alliance_id=2), user_id="u1", db=db)
    row = db.execute(text("SELECT * FROM alliance_treaties")).fetchone()
    assert res["status"] == "proposed" and row is not None
