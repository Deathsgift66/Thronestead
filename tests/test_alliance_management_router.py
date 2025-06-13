import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import User, Kingdom, KingdomResources, Alliance
from backend.routers.alliance_management import (
    create_alliance,
    delete_alliance,
    CreatePayload,
    DeletePayload,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user_with_resources(db):
    uid = str(uuid.uuid4())
    db.add(Kingdom(kingdom_id=1, user_id=uid, kingdom_name="K"))
    db.add(KingdomResources(kingdom_id=1, wood=2000, stone=2000, gold=1000))
    user = User(user_id=uid, username="t", display_name="T", email="t@test.com", kingdom_id=1)
    db.add(user)
    db.commit()
    return uid


def test_create_alliance_deducts_resources():
    Session = setup_db()
    db = Session()
    uid = create_user_with_resources(db)
    res = create_alliance(CreatePayload(name="A"), uid, db)
    aid = res["alliance_id"]
    alliance = db.query(Alliance).filter_by(alliance_id=aid).first()
    assert alliance and alliance.name == "A"
    resources = db.query(KingdomResources).filter_by(kingdom_id=1).first()
    assert resources.wood == 1000 and resources.stone == 1000 and resources.gold == 500
    user = db.query(User).filter_by(user_id=uid).first()
    assert user.alliance_id == aid and user.alliance_role == "Leader"


def test_delete_alliance_removes_records():
    Session = setup_db()
    db = Session()
    uid = create_user_with_resources(db)
    res = create_alliance(CreatePayload(name="B"), uid, db)
    aid = res["alliance_id"]
    delete_alliance(DeletePayload(alliance_id=aid), uid, db)
    assert db.query(Alliance).filter_by(alliance_id=aid).first() is None
    user = db.query(User).filter_by(user_id=uid).first()
    assert user.alliance_id is None
