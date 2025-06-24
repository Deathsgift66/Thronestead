from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Kingdom, KingdomResources, KingdomSpies
from backend.routers.spy import LaunchPayload, launch_spy_mission
from services.spies_service import get_spy_defense, reset_daily_attack_counts
from services import spies_service
import random


class DummyResult:
    def __init__(self, rowcount=0):
        self.rowcount = rowcount


class DummyDB:
    def __init__(self, row=None):
        self.queries = []
        self.committed = False
        self.row = row

    def execute(self, query, params=None):
        self.queries.append(str(query).strip())
        if "spy_defense" in str(query):

            class R:
                def fetchone(_self):
                    return self.row

            return R()
        return DummyResult(rowcount=5)

    def commit(self):
        self.committed = True


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    # minimal spy_defense table for detection tests
    engine.execute(
        text(
            "CREATE TABLE spy_defense (kingdom_id INTEGER PRIMARY KEY, detection_level INTEGER DEFAULT 1, daily_spy_detections INTEGER DEFAULT 0)"
        )
    )
    return Session


def test_reset_daily_attack_counts():
    db = DummyDB()
    count = reset_daily_attack_counts(db)
    assert count == 5
    assert any("UPDATE kingdom_spies" in q for q in db.queries)
    assert db.committed


def test_get_spy_defense_returns_value():
    db = DummyDB(row=(3,))
    rating = get_spy_defense(db, 1)
    assert rating == 3
    assert any("spy_defense" in q for q in db.queries)


def test_get_spy_defense_default_zero():
    db = DummyDB(row=None)
    rating = get_spy_defense(db, 2)
    assert rating == 0


def test_train_spies_updates_resources():
    Session = setup_db()
    db = Session()
    db.add(Kingdom(kingdom_id=1, user_id="u1", kingdom_name="K"))
    db.add(KingdomResources(kingdom_id=1, gold=1000))
    db.add(KingdomSpies(kingdom_id=1, spy_count=2, max_spy_capacity=10, spy_xp=0, spy_upkeep_gold=0))
    db.commit()

    spies_service.train_spies(db, 1, 3)

    rec = db.query(KingdomSpies).filter_by(kingdom_id=1).one()
    res = db.query(KingdomResources).filter_by(kingdom_id=1).one()

    assert rec.spy_count == 5
    assert rec.spy_xp == 15
    assert rec.spy_upkeep_gold == 3
    assert res.gold == 1000 - 3 * spies_service.SPY_TRAIN_COST_GOLD


def test_detection_increments_counter(monkeypatch):
    Session = setup_db()
    db = Session()
    db.add_all([
        Kingdom(kingdom_id=1, user_id="u1", kingdom_name="A", tech_level=1),
        Kingdom(kingdom_id=2, user_id="u2", kingdom_name="B", tech_level=1),
        KingdomSpies(kingdom_id=1, spy_count=5, spy_xp=0),
        KingdomSpies(kingdom_id=2, spy_count=5, spy_xp=0),
        KingdomResources(kingdom_id=1, gold=1000),
    ])
    db.execute(text("INSERT INTO spy_defense (kingdom_id, detection_level) VALUES (2, 1)"))
    db.commit()

    monkeypatch.setattr(random, "random", lambda: 0.0)
    monkeypatch.setattr(random, "randint", lambda a, b: a)
    monkeypatch.setattr(spies_service, "finalize_mission", lambda *a, **k: None)

    launch_spy_mission(
        LaunchPayload(target_kingdom_name="B", mission_type="scout", num_spies=1),
        user_id="u1",
        db=db,
    )

    row = db.execute(text("SELECT daily_spy_detections FROM spy_defense WHERE kingdom_id=2")).fetchone()
    assert row[0] == 1
