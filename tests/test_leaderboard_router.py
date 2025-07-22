# Project Name: Thronestead©
# File Name: test_leaderboard_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Alliance, AllianceWar, AllianceWarScore, User
from backend.routers import leaderboard


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_alliance_leaderboard_returns_stats_and_self():
    Session = setup_db()
    db = Session()
    db.add_all(
        [
            Alliance(
                alliance_id=1,
                name="A",
                military_score=10,
                economy_score=5,
                diplomacy_score=2,
            ),
            Alliance(
                alliance_id=2,
                name="B",
                military_score=8,
                economy_score=7,
                diplomacy_score=3,
            ),
            AllianceWar(
                alliance_war_id=1, attacker_alliance_id=1, defender_alliance_id=2
            ),
            AllianceWarScore(
                alliance_war_id=1, attacker_score=5, defender_score=2, victor="attacker"
            ),
            User(user_id="u1", username="x", kingdom_name="k", alliance_id=1),
        ]
    )
    db.commit()

    result = leaderboard.get_leaderboard("alliances", user_id="u1", db=db)
    assert result["entries"][0]["war_wins"] == 1
    assert result["entries"][0]["is_self"] is True


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []

    def select(self, *_):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, n):
        self._data = self._data[:n]
        return self

    def execute(self):
        return {"data": self._data}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_kingdom_leaderboard_marks_self_and_limit():
    data = [
        {"user_id": "u1", "kingdom_name": "A", "ruler_name": "r1", "rank": 1},
        {"user_id": "u2", "kingdom_name": "B", "ruler_name": "r2", "rank": 2},
    ]
    leaderboard.get_supabase_client = lambda: DummyClient(
        {"leaderboard_kingdoms": data}
    )
    result = leaderboard.get_leaderboard("kingdoms", limit=1, user_id="u1", db=None)
    assert len(result["entries"]) == 1
    assert result["entries"][0]["is_self"] is True


def test_leaderboard_excludes_banned():
    data = [
        {"user_id": "u1", "kingdom_name": "A", "rank": 1, "is_banned": True},
        {"user_id": "u2", "kingdom_name": "B", "rank": 2},
    ]
    leaderboard.get_supabase_client = lambda: DummyClient(
        {"leaderboard_kingdoms": data}
    )
    result = leaderboard.get_leaderboard("kingdoms", limit=10, user_id=None, db=None)
    assert len(result["entries"]) == 1
    assert result["entries"][0]["user_id"] == "u2"
