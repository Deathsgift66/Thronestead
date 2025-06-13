# Project Name: Kingmakers Rise©
# File Name: test_alliance_wars_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import User, AllianceWar, AllianceWarPreplan
from backend.routers.alliance_wars import (
    list_wars,
    submit_preplan,
    get_preplan,
    declare_war,
    respond_war,
    list_active_wars,
    request_join,
    surrender_war,
    DeclarePayload,
    RespondPayload,
    JoinPayload,
    SurrenderPayload,
)


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


def test_get_preplan_returns_plan():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    db.add(AllianceWar(alliance_war_id=6, attacker_alliance_id=1, defender_alliance_id=2, war_status="preplan", phase="preplan"))
    db.add(AllianceWarPreplan(alliance_war_id=6, kingdom_id=1, preplan_jsonb={"units": ["a"]}))
    db.commit()

    res = get_preplan(6, user_id=uid, db=db)
    assert res["plan"] == {"units": ["a"]}


def test_declare_war_creates_record():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)

    res = declare_war(DeclarePayload(defender_alliance_id=2), user_id=uid, db=db)
    row = db.query(AllianceWar).filter_by(attacker_alliance_id=1, defender_alliance_id=2).first()
    assert row is not None
    assert row.war_status == "pending"
    assert res["status"] == "pending"


def test_accept_war_updates_status():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    db.add(AllianceWar(alliance_war_id=10, attacker_alliance_id=2, defender_alliance_id=1, war_status="pending", phase="alert"))
    db.commit()

    respond_war(RespondPayload(alliance_war_id=10, action="accept"), user_id=uid, db=db)
    row = db.query(AllianceWar).filter_by(alliance_war_id=10).first()
    assert row.war_status == "active"


def test_join_war_increments_battles():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    db.add(AllianceWar(alliance_war_id=20, attacker_alliance_id=1, defender_alliance_id=2, war_status="active", phase="battle"))
    db.commit()
    request_join(JoinPayload(alliance_war_id=20, side="attacker"), user_id=uid, db=db)
    score = db.execute(text("SELECT battles_participated FROM alliance_war_scores WHERE alliance_war_id = :wid"), {"wid": 20}).fetchone()
    assert score[0] == 1


def test_surrender_updates_victor():
    Session = setup_db()
    db = Session()
    uid = seed_user(db)
    db.add(AllianceWar(alliance_war_id=30, attacker_alliance_id=1, defender_alliance_id=2, war_status="active", phase="battle"))
    db.commit()
    surrender_war(SurrenderPayload(alliance_war_id=30, side="attacker"), user_id=uid, db=db)
    war = db.query(AllianceWar).filter_by(alliance_war_id=30).first()
    assert war.war_status == "surrendered"
    score = db.execute(text("SELECT victor FROM alliance_war_scores WHERE alliance_war_id = :wid"), {"wid": 30}).fetchone()
    assert score[0] == "defender"


def test_active_wars_endpoint_lists_active():
    Session = setup_db()
    db = Session()
    seed_user(db)
    db.add(AllianceWar(alliance_war_id=40, attacker_alliance_id=1, defender_alliance_id=2, war_status="active", phase="battle"))
    db.add(AllianceWar(alliance_war_id=41, attacker_alliance_id=1, defender_alliance_id=3, war_status="pending", phase="alert"))
    db.commit()
    res = list_active_wars(db=db)
    assert len(res["wars"]) == 1
