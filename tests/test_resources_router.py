from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import User, KingdomResources
from backend.routers.resources import get_resources


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_data(db):
    user = User(
        user_id="u1",
        username="tester",
        display_name="Tester",
        email="t@example.com",
        kingdom_id=1,
    )
    db.add(user)
    db.add(KingdomResources(kingdom_id=1, wood=100, gold=50))
    db.commit()
    return user.user_id


def test_get_resources_returns_row():
    Session = setup_db()
    db = Session()
    uid = seed_data(db)

    res = get_resources(user_id=uid, db=db)
    assert res["resources"]["wood"] == 100
    assert res["resources"]["gold"] == 50
