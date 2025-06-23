from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Kingdom, User, War
from backend.routers.wars import DeclarePayload, declare_war
from models.progression import KingdomKnight


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_declare_war_persists_record():
    Session = setup_db()
    db = Session()

    db.add_all(
        [
            User(user_id="a1", username="A", email="a@example.com", kingdom_id=1),
            User(user_id="d1", username="D", email="d@example.com", kingdom_id=2),
            Kingdom(kingdom_id=1, user_id="a1", kingdom_name="Aking"),
            Kingdom(kingdom_id=2, user_id="d1", kingdom_name="Dking"),
            KingdomKnight(kingdom_id=1, name="Sir A"),
        ]
    )
    db.commit()

    res = declare_war(
        DeclarePayload(target="d1", war_reason="testing"), user_id="a1", db=db
    )
    war = db.query(War).first()
    assert war is not None
    assert war.defender_id == "d1"
    assert res["war_id"] == war.war_id
