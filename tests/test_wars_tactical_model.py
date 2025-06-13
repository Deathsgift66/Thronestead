# Project Name: Kingmakers Rise©
# File Name: test_wars_tactical_model.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import WarsTactical, War


def test_wars_tactical_model_creation():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = Session()

    base_war = War(attacker_name="A", defender_name="B", status="active")
    db.add(base_war)
    db.flush()
    wt = WarsTactical(war_id=base_war.war_id, attacker_kingdom_id=1, defender_kingdom_id=2, phase="alert")
    db.add(wt)
    db.commit()

    saved = db.query(WarsTactical).first()
    assert saved.war_id == 1
    assert saved.phase == "alert"
