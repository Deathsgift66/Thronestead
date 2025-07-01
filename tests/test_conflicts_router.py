# Comment
# Project Name: Thronestead©
# File Name: test_conflicts_router.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import User
from backend.routers import conflicts


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []
        self._single = False

    def select(self, *_args):
        return self

    def or_(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._single:
            return {"data": self._data[0] if self._data else None}
        return {"data": self._data}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.queries = []
        self.rows = []

    def execute(self, query, params=None):
        self.queries.append((str(query), params))
        return DummyResult(self.rows)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_user(db):
    uid = "u1"
    user = User(
        user_id=uid,
        username="t",
        display_name="T",
        email="t@example.com",
        kingdom_id=1,
        alliance_id=2,
    )
    db.add(user)
    db.commit()
    return uid


def test_list_kingdom_wars_returns_rows():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    wars = [
        {
            "war_id": 5,
            "attacker_kingdom_id": 1,
            "defender_kingdom_id": 99,
            "attacker_name": "A",
            "defender_name": "B",
        }
    ]
    conflicts.get_supabase_client = lambda: DummyClient({"wars": wars})
    result = conflicts.list_kingdom_wars(user_id=uid, db=db)
    assert result["wars"][0]["war_id"] == 5


def test_get_war_details_denies_unrelated():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    war = {"war_id": 2, "attacker_kingdom_id": 3, "defender_kingdom_id": 4}
    conflicts.get_supabase_client = lambda: DummyClient(
        {"wars": [war], "war_scores": []}
    )
    try:
        conflicts.get_war_details(2, user_id=uid, db=db)
    except HTTPException as e:
        assert e.status_code == 403
    else:
        assert False


def test_list_conflict_overview_executes_query():
    db = DummyDB()
    db.rows = [
        (
            1,
            "duel",
            "live",
            3,
            900,
            "2025-01-01",
            "A",
            "B",
            "AllA",
            "AllB",
            None,
            5,
            4,
            None,
        )
    ]
    result = conflicts.list_conflict_overview(db=db, user_id="u1")
    assert result["wars"][0]["war_id"] == 1
    joined = " ".join(db.queries[0][0].lower().split())
    assert "from wars_tactical" in joined


def test_list_all_conflicts_executes_query():
    db = DummyDB()
    db.rows = [
        (
            1,
            "AllA",
            "AllB",
            "duel",
            "2025-01-01",
            "active",
            900,
            5,
            4,
            "attacker",
        )
    ]
    result = conflicts.list_all_conflicts(db=db, user_id="u1")
    assert result["wars"][0]["war_id"] == 1
    assert db.queries


def test_get_conflict_details_returns_row():
    db = DummyDB()
    db.rows = [
        (
            1,
            "AllA",
            "AllB",
            "duel",
            "2025-01-01",
            "active",
            900,
            5,
            4,
            "attacker",
        )
    ]
    result = conflicts.get_conflict_details(1, db=db, user_id="u1")
    assert result["war"]["war_id"] == 1


def test_search_conflicts_uses_param():
    db = DummyDB()
    db.rows = []
    conflicts.search_conflicts(q="test", db=db, user_id="u1")
    assert db.queries[0][1]["s"].startswith("%test")


def test_filter_conflicts_binds_phase():
    db = DummyDB()
    db.rows = []
    conflicts.filter_conflicts({"status": "active"}, db=db, user_id="u1")
    assert db.queries[0][1]["phase"] == "active"
