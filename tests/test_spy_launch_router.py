from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random

from backend.db_base import Base
from backend.models import (
    User,
    Kingdom,
    KingdomSpies,
    SpyMissions,
    VillageModifier,
    KingdomVillage,
)
from backend.routers.spy import launch_spy_mission, LaunchPayload


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_data(db):
    db.add_all([
        User(user_id="u1", username="A", email="a@example.com", kingdom_id=1),
        User(user_id="u2", username="B", email="b@example.com", kingdom_id=2),
        Kingdom(kingdom_id=1, user_id="u1", kingdom_name="Aking", tech_level=2),
        Kingdom(kingdom_id=2, user_id="u2", kingdom_name="Bking", tech_level=1),
        KingdomSpies(kingdom_id=1, spy_count=5),
        KingdomSpies(kingdom_id=2, spy_count=5),
        KingdomVillage(village_id=1, kingdom_id=2, village_name="V")
    ])
    db.add(VillageModifier(village_id=1))
    db.commit()


def test_launch_spy_mission_inserts_row(monkeypatch):
    Session = setup_db()
    db = Session()
    seed_data(db)

    monkeypatch.setattr(random, "random", lambda: 0.01)
    monkeypatch.setattr(random, "randint", lambda a, b: a)

    res = launch_spy_mission(
        LaunchPayload(target_kingdom_name="Bking", mission_type="scout", num_spies=3),
        user_id="u1",
        db=db,
    )

    mission = db.query(SpyMissions).first()
    assert mission is not None
    assert res["mission_id"] == mission.mission_id
    assert res["outcome"] in {"success", "failed"}

