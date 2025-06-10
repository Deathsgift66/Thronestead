from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import WarsTactical


def test_wars_tactical_model_creation():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = Session()

    wt = WarsTactical(attacker_kingdom_id=1, defender_kingdom_id=2, phase="alert")
    db.add(wt)
    db.commit()

    saved = db.query(WarsTactical).first()
    assert saved.war_id == 1
    assert saved.phase == "alert"
