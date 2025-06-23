from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Alliance, AllianceWar
from backend.routers.alliance_wars import (
    DeclarePayload,
    RespondPayload,
    SurrenderPayload,
    declare_war,
    list_active_wars,
    list_wars,
    respond_war,
    surrender_war,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_alliance(db, aid):
    db.add(Alliance(alliance_id=aid, name=f"A{aid}"))
    db.commit()


def test_list_wars_groups_by_status():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    seed_alliance(db, 3)
    db.add(
        AllianceWar(
            attacker_alliance_id=1,
            defender_alliance_id=2,
            war_status="active",
            phase="battle",
        )
    )
    db.add(
        AllianceWar(
            attacker_alliance_id=1,
            defender_alliance_id=3,
            war_status="completed",
            phase="resolution",
        )
    )
    db.commit()

    res = list_wars(1, db=db)
    assert len(res["active_wars"]) == 1
    assert len(res["completed_wars"]) == 1


def test_declare_war_creates_record():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)

    res = declare_war(
        DeclarePayload(attacker_alliance_id=1, defender_alliance_id=2), db=db
    )
    row = (
        db.query(AllianceWar)
        .filter_by(attacker_alliance_id=1, defender_alliance_id=2)
        .first()
    )
    assert row is not None
    assert row.war_status == "pending"
    assert res["status"] == "pending"


def test_accept_war_updates_status():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    db.add(
        AllianceWar(
            alliance_war_id=10,
            attacker_alliance_id=2,
            defender_alliance_id=1,
            war_status="pending",
            phase="alert",
        )
    )
    db.commit()

    respond_war(RespondPayload(alliance_war_id=10, action="accept"), db=db)
    row = db.query(AllianceWar).filter_by(alliance_war_id=10).first()
    assert row.war_status == "active"


def test_surrender_updates_status():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    db.add(
        AllianceWar(
            alliance_war_id=30,
            attacker_alliance_id=1,
            defender_alliance_id=2,
            war_status="active",
            phase="battle",
        )
    )
    db.commit()
    surrender_war(SurrenderPayload(alliance_war_id=30, side="attacker"), db=db)
    war = db.query(AllianceWar).filter_by(alliance_war_id=30).first()
    assert war.war_status == "surrendered"


def test_active_wars_endpoint_lists_active():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    seed_alliance(db, 3)
    db.add(
        AllianceWar(
            alliance_war_id=40,
            attacker_alliance_id=1,
            defender_alliance_id=2,
            war_status="active",
            phase="battle",
        )
    )
    db.add(
        AllianceWar(
            alliance_war_id=41,
            attacker_alliance_id=1,
            defender_alliance_id=3,
            war_status="pending",
            phase="alert",
        )
    )
    db.commit()
    res = list_active_wars(db=db)
    assert len(res["wars"]) == 1
