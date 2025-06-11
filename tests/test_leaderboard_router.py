import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Alliance, AllianceWar, AllianceWarScore
from backend.routers import leaderboard


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_alliance_leaderboard_returns_stats():
    Session = setup_db()
    db = Session()
    db.add(Alliance(alliance_id=1, name="A", military_score=10, economy_score=5, diplomacy_score=2))
    db.add(Alliance(alliance_id=2, name="B", military_score=8, economy_score=7, diplomacy_score=3))
    db.add(AllianceWar(alliance_war_id=1, attacker_alliance_id=1, defender_alliance_id=2))
    db.add(AllianceWarScore(alliance_war_id=1, attacker_score=5, defender_score=2, victor="attacker"))
    db.commit()

    result = asyncio.run(leaderboard.leaderboard("alliances", user_id="u1", db=db))
    assert result["entries"][0]["war_wins"] == 1
    assert result["entries"][0]["military_score"] == 10
