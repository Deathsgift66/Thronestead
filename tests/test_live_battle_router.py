from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import CombatLog, TerrainMap, UnitMovement, WarScore, WarsTactical
from backend.routers.battle import get_live_battle


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_get_live_battle_returns_data():
    Session = setup_db()
    db = Session()

    db.add(
        WarsTactical(
            war_id=1,
            attacker_kingdom_id=1,
            defender_kingdom_id=2,
            phase="live",
            castle_hp=90,
            battle_tick=5,
            tick_interval_seconds=60,
            fog_of_war=True,
            weather="clear",
        )
    )
    db.add(
        TerrainMap(
            terrain_id=1, war_id=1, tile_map=[["field"]], map_width=1, map_height=1
        )
    )
    db.add(
        UnitMovement(
            movement_id=1,
            war_id=1,
            kingdom_id=1,
            unit_type="infantry",
            quantity=20,
            position_x=0,
            position_y=0,
        )
    )
    db.add(
        CombatLog(
            combat_id=1, war_id=1, tick_number=5, event_type="attack", damage_dealt=3
        )
    )
    db.add(WarScore(war_id=1, attacker_score=5, defender_score=1, victor=None))
    db.commit()

    result = get_live_battle(1, db=db, user_id="u1")
    assert result["war_id"] == 1
    assert result["units"][0]["movement_id"] == 1
    assert result["combat_logs"][0]["event_type"] == "attack"
    assert result["attacker_score"] == 5
    assert result["map_width"] == 1


def test_get_live_battle_404():
    Session = setup_db()
    db = Session()
    try:
        get_live_battle(99, db=db, user_id="u1")
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        assert False
