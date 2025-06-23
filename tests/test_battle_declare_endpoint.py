from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Alliance, AllianceWar, User
from backend.routers.battle import declare_alliance_battle, DeclarePayload


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_declare_alliance_battle_creates_war():
    Session = setup_db()
    db = Session()
    db.add_all([
        Alliance(alliance_id=1, name="A"),
        Alliance(alliance_id=2, name="B"),
        User(user_id="u1", username="User", email="u@test.com", kingdom_name="K", alliance_id=1),
    ])
    db.commit()

    res = declare_alliance_battle(DeclarePayload(target_alliance_id=2), user_id="u1", db=db)
    war = db.query(AllianceWar).filter_by(attacker_alliance_id=1, defender_alliance_id=2).first()
    assert war is not None
    assert res["success"] is True


def test_declare_alliance_battle_no_alliance():
    Session = setup_db()
    db = Session()
    db.add_all([
        Alliance(alliance_id=2, name="B"),
        User(user_id="u1", username="User", email="u@test.com", kingdom_name="K"),
    ])
    db.commit()

    try:
        declare_alliance_battle(DeclarePayload(target_alliance_id=2), user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        assert False
