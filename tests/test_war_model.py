# Project Name: Thronestead©
# File Name: test_war_model.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import War


def test_war_model_basic():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = Session()

    war = War(
        attacker_name="A",
        defender_name="D",
        status="pending",
        war_type="duel",
        victory_condition="score",
    )
    db.add(war)
    db.commit()

    saved = db.query(War).first()
    assert saved.war_id == 1
    assert saved.status == "pending"
