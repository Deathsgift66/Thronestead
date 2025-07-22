from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import (
    Alliance,
    AllianceMember,
    Kingdom,
    KingdomVillage,
    User,
    VillageProduction,
)
from backend.routers.alliance_members_api import list_members


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_data(db):
    db.add(Alliance(alliance_id=1, name="A"))
    db.add(
        User(
            user_id="u1",
            username="Leader",
            email="l@test.com",
            alliance_id=1,
            kingdom_id=1,
        )
    )
    db.add(
        User(
            user_id="u2",
            username="LeoTheBrave",
            email="b@test.com",
            alliance_id=1,
            kingdom_id=2,
        )
    )
    db.add(
        Kingdom(
            kingdom_id=1,
            user_id="u1",
            kingdom_name="K1",
            military_score=10,
            economy_score=20,
            diplomacy_score=5,
        )
    )
    db.add(
        Kingdom(
            kingdom_id=2,
            user_id="u2",
            kingdom_name="K2",
            military_score=120,
            economy_score=880,
            diplomacy_score=400,
        )
    )
    db.add(
        AllianceMember(
            alliance_id=1,
            user_id="u1",
            username="Leader",
            rank="Leader",
            contribution=100,
        )
    )
    db.add(
        AllianceMember(
            alliance_id=1,
            user_id="u2",
            username="LeoTheBrave",
            rank="officer",
            contribution=3200,
        )
    )
    db.add(KingdomVillage(village_id=1, kingdom_id=2, village_name="V1"))
    db.add(VillageProduction(village_id=1, resource_type="wood", production_rate=785))
    db.commit()


def test_list_members_returns_joined_scores():
    Session = setup_db()
    db = Session()
    seed_data(db)

    result = list_members(
        sort_by="military_score", direction="desc", search="Leo", user_id="u1", db=db
    )
    assert len(result) == 1
    m = result[0]
    assert m["username"] == "LeoTheBrave"
    assert m["military_score"] == 120
    assert m["total_output"] == 785
