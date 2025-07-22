from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Alliance, AllianceWar, AllianceWarScore, User
from backend.routers.battle import list_alliance_wars


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_list_alliance_wars_returns_active():
    Session = setup_db()
    db = Session()
    db.add_all([
        Alliance(alliance_id=1, name="A1"),
        Alliance(alliance_id=2, name="A2"),
        User(user_id="u1", username="x", email="x@e.com", kingdom_name="k", alliance_id=1),
        AllianceWar(
            alliance_war_id=1,
            attacker_alliance_id=1,
            defender_alliance_id=2,
            phase="live",
            war_status="active",
        ),
        AllianceWarScore(alliance_war_id=1, attacker_score=10, defender_score=3),
    ])
    db.commit()

    res = list_alliance_wars(user_id="u1", db=db)
    assert len(res) == 1
    war = res[0]
    assert war["enemy_name"] == "A2"
    assert war["phase"] == "live"
    assert war["our_score"] == 10
    assert war["their_score"] == 3


def test_list_alliance_wars_404_no_alliance():
    Session = setup_db()
    db = Session()
    db.add(User(user_id="u1", username="x", email="x@e.com", kingdom_name="k"))
    db.commit()
    try:
        list_alliance_wars(user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        assert False
