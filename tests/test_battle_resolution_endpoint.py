from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from backend.db_base import Base
from backend.models import (
    WarScore, BattleResolutionLog, WarsTactical, Kingdom, User, CombatLog
)
from backend.routers.battle import battle_resolution_alt


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_data(db):
    db.add_all([
        Kingdom(kingdom_id=1, kingdom_name="Northreach"),
        Kingdom(kingdom_id=2, kingdom_name="Stormhold"),
        User(user_id="u1", username="P", email="p@test.com", kingdom_id=1),
        WarsTactical(war_id=1, attacker_kingdom_id=1, defender_kingdom_id=2),
        WarScore(war_id=1, attacker_score=50, defender_score=30, victor="attacker"),
        BattleResolutionLog(
            war_id=1,
            winner_side="attacker",
            total_ticks=11,
            attacker_casualties=3,
            defender_casualties=5,
            loot_summary={"gold": 100},
        ),
        CombatLog(war_id=1, tick_number=1, event_type="start"),
        CombatLog(war_id=1, tick_number=2, event_type="end", notes="done"),
    ])
    db.commit()


def test_battle_resolution_alt_returns_data():
    Session = setup_db()
    db = Session()
    seed_data(db)

    res = battle_resolution_alt(1, db=db, user_id="u1")
    assert res["winner"] == "attacker"
    assert res["victor_score"] == 50
    assert res["loot"]["gold"] == 100
    assert res["participants"]["attacker"] == ["Northreach"]
    assert res["participants"]["defender"] == ["Stormhold"]
    assert len(res["timeline"]) == 2


def test_battle_resolution_alt_forbidden():
    Session = setup_db()
    db = Session()
    seed_data(db)
    db.add(User(user_id="u2", username="O", email="o@test.com", kingdom_id=3))
    db.commit()

    try:
        battle_resolution_alt(1, db=db, user_id="u2")
    except HTTPException as e:
        assert e.status_code == 403
    else:
        assert False
