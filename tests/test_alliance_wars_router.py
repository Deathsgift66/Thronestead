from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import User, AllianceWar, AllianceWarPreplan
from backend.routers.alliance_wars import list_wars, submit_preplan


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_user(db):
    user = User(
        user_id="00000000-0000-0000-0000-000000000001",
        username="tester",
        display_name="Tester",
        email="t@example.com",
        kingdom_id=1,
        alliance_id=1,
    )
    db.add(user)
    db.commit()
    return user.user_id


def test_list_wars_groups_by_status():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    db.add(AllianceWar(alliance_war_id=1, attacker_alliance_id=1, defender_alliance_id=2, war_status="active", phase="battle"))
    db.add(AllianceWar(alliance_war_id=2, attacker_alliance_id=1, defender_alliance_id=3, war_status="completed", phase="resolution"))
    db.commit()

    res = list_wars(user_id=uid, db=db)
    assert len(res["active_wars"]) == 1
    assert len(res["completed_wars"]) == 1


def test_submit_preplan_upserts():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    db.add(AllianceWar(alliance_war_id=5, attacker_alliance_id=1, defender_alliance_id=2, war_status="preplan", phase="preplan"))
    db.commit()

    submit_preplan(5, {"units": []}, user_id=uid, db=db)
    row = db.query(AllianceWarPreplan).filter_by(alliance_war_id=5, kingdom_id=1).first()
    assert row is not None
    assert row.preplan_jsonb == {"units": []}
