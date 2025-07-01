# Project Name: Thronestead©
# File Name: test_wars_tactical_model.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import War, WarsTactical


def test_wars_tactical_model_creation():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = Session()

    base_war = War(attacker_name="A", defender_name="B", status="active")
    db.add(base_war)
    db.flush()
    wt = WarsTactical(
        war_id=base_war.war_id,
        attacker_kingdom_id=1,
        defender_kingdom_id=2,
        phase="alert",
    )
    db.add(wt)
    db.commit()

    saved = db.query(WarsTactical).first()
    assert saved.war_id == 1
    assert saved.phase == "alert"
