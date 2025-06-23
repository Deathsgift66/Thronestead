# Project Name: Thronestead©
# File Name: test_battle_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import WarScore
from backend.routers.battle import get_battle_scoreboard


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_get_battle_scoreboard_returns_scores():
    Session = setup_db()
    db = Session()
    db.add(WarScore(war_id=1, attacker_score=10, defender_score=5, victor="attacker"))
    db.commit()

    result = get_battle_scoreboard(1, db=db, user_id="u1")
    assert result["attacker_score"] == 10
    assert result["defender_score"] == 5
    assert result["victor"] == "attacker"


def test_get_battle_scoreboard_404():
    Session = setup_db()
    db = Session()
    try:
        get_battle_scoreboard(99, db=db, user_id="u1")
    except HTTPException as e:
        assert e.status_code == 404
    else:
        assert False
