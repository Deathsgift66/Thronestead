from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import (
    Alliance,
    AllianceRole,
    AllianceMember,
    User,
    Kingdom,
    AllianceWar,
    AllianceWarParticipant,
    AllianceWarPreplan,
)
from backend.routers.alliance_wars import (
    PreplanPayload,
    PreplanData,
    Point,
    get_preplan,
    submit_preplan,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_basic_war(db):
    db.add_all(
        [
            Alliance(alliance_id=1, name="A"),
            Alliance(alliance_id=2, name="B"),
            AllianceRole(role_id=1, alliance_id=1, role_name="Leader", permissions=[]),
            AllianceMember(alliance_id=1, user_id="u1", username="U1", role_id=1),
            User(user_id="u1", username="U1", email="u1@test.com", kingdom_id=1, alliance_id=1),
            Kingdom(kingdom_id=1, user_id="u1", kingdom_name="K1", alliance_id=1),
            AllianceRole(role_id=2, alliance_id=2, role_name="Leader", permissions=[]),
            AllianceMember(alliance_id=2, user_id="u2", username="U2", role_id=2),
            User(user_id="u2", username="U2", email="u2@test.com", kingdom_id=2, alliance_id=2),
            Kingdom(kingdom_id=2, user_id="u2", kingdom_name="K2", alliance_id=2),
            AllianceWar(
                alliance_war_id=1,
                attacker_alliance_id=1,
                defender_alliance_id=2,
                war_status="active",
                phase="live",
            ),
            AllianceWarParticipant(alliance_war_id=1, kingdom_id=1, role="attacker"),
        ]
    )
    db.commit()


def test_get_preplan_forbidden():
    Session = setup_db()
    db = Session()
    seed_basic_war(db)
    try:
        get_preplan(1, user_id="u2", db=db)
    except HTTPException as e:
        assert e.status_code == 403
    else:
        assert False


def test_submit_preplan_creates_record():
    Session = setup_db()
    db = Session()
    seed_basic_war(db)

    payload = PreplanPayload(
        alliance_war_id=1,
        preplan_jsonb=PreplanData(
            fallback_point=Point(x=1, y=2),
            patrol_path=[Point(x=0, y=0)],
        ),
    )

    submit_preplan(payload, user_id="u1", db=db)
    row = db.query(AllianceWarPreplan).filter_by(alliance_war_id=1, kingdom_id=1).first()
    assert row is not None
    assert row.preplan_jsonb["fallback_point"]["x"] == 1

