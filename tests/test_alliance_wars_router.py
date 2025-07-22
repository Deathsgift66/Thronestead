from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from backend.database import Base
from backend.models import (
    Alliance,
    AllianceWar,
    AllianceMember,
    AllianceRole,
    User,
    Kingdom,
    TroopSlots,
    UnitMovement,
)
from backend.routers.alliance_wars import (
    DeclarePayload,
    RespondPayload,
    SurrenderPayload,
    JoinPayload,
    declare_war,
    list_active_wars,
    list_wars,
    respond_war,
    surrender_war,
    join_war,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_alliance(db, aid):
    db.add(Alliance(alliance_id=aid, name=f"A{aid}"))
    db.commit()


def seed_member(db, aid, uid, perms):
    role_id = aid
    db.add(AllianceRole(role_id=role_id, alliance_id=aid, role_name="Leader", permissions=perms))
    db.add(AllianceMember(alliance_id=aid, user_id=uid, username="U", role_id=role_id))
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
            phase="live",
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
    seed_member(db, 1, "u1", ["can_manage_wars"])

    res = declare_war(
        DeclarePayload(attacker_alliance_id=1, defender_alliance_id=2),
        user_id="u1",
        db=db,
    )
    row = (
        db.query(AllianceWar)
        .filter_by(attacker_alliance_id=1, defender_alliance_id=2)
        .first()
    )
    assert row is not None
    assert row.war_status == "pending"
    assert res["status"] == "pending"


def test_declare_war_forbidden():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    seed_member(db, 1, "u1", ["can_manage_wars"])
    try:
        declare_war(
            DeclarePayload(attacker_alliance_id=2, defender_alliance_id=1),
            user_id="u1",
            db=db,
        )
    except HTTPException as e:
        assert e.status_code == 403
    else:
        assert False


def test_accept_war_updates_status():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    seed_member(db, 1, "u1", ["can_manage_wars"])
    seed_member(db, 2, "u2", ["can_manage_wars"])
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

    respond_war(
        RespondPayload(alliance_war_id=10, action="accept"),
        user_id="u1",
        db=db,
    )
    row = db.query(AllianceWar).filter_by(alliance_war_id=10).first()
    assert row.war_status == "active"


def test_surrender_updates_status():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    seed_member(db, 1, "u1", ["can_manage_wars"])
    seed_member(db, 2, "u2", ["can_manage_wars"])
    db.add(
        AllianceWar(
            alliance_war_id=30,
            attacker_alliance_id=1,
            defender_alliance_id=2,
            war_status="active",
            phase="live",
        )
    )
    db.commit()
    surrender_war(
        SurrenderPayload(alliance_war_id=30, side="attacker"),
        user_id="u1",
        db=db,
    )
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
            phase="live",
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


def test_join_war_forbidden():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    seed_member(db, 1, "u1", ["can_join_wars"])
    db.add(
        AllianceWar(
            alliance_war_id=50,
            attacker_alliance_id=2,
            defender_alliance_id=1,
            war_status="active",
            phase="battle",
        )
    )
    db.commit()
    try:
        join_war(
            JoinPayload(alliance_war_id=50, side="attacker"),
            user_id="u1",
            db=db,
        )
    except HTTPException as e:
        assert e.status_code == 403
    else:
        assert False


def test_join_war_inserts_movement_with_morale():
    Session = setup_db()
    db = Session()
    seed_alliance(db, 1)
    seed_alliance(db, 2)
    seed_member(db, 1, "u1", ["can_join_wars"])
    db.add_all(
        [
            User(user_id="u1", username="U", email="u@test.com", kingdom_id=1, alliance_id=1),
            Kingdom(kingdom_id=1, user_id="u1", kingdom_name="K1", alliance_id=1),
            TroopSlots(kingdom_id=1, morale=90, morale_bonus_buildings=5, morale_bonus_tech=10),
            AllianceWar(
                alliance_war_id=60,
                attacker_alliance_id=1,
                defender_alliance_id=2,
                war_status="active",
                phase="live",
            ),
        ]
    )
    db.commit()

    join_war(JoinPayload(alliance_war_id=60, side="attacker"), user_id="u1", db=db)
    movement = db.query(UnitMovement).filter_by(war_id=60, kingdom_id=1).first()
    assert movement is not None
    assert movement.morale == 100
