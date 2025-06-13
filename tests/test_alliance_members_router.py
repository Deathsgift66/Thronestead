# Project Name: Kingmakers Rise©
# File Name: test_alliance_members_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import AllianceMember, Alliance
from backend.routers.alliance_members import (
    promote,
    RankPayload,
    transfer_leadership,
    TransferLeadershipPayload,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_promote_updates_rank():
    Session = setup_db()
    db = Session()
    db.add(AllianceMember(alliance_id=1, user_id="u1", username="A", rank="Member"))
    db.commit()

    promote(RankPayload(user_id="u1", alliance_id=1, new_rank="Leader"), user_id="admin", db=db)
    row = db.query(AllianceMember).filter_by(user_id="u1").first()
    assert row.rank == "Leader"

import pytest
from fastapi import HTTPException
from backend.routers.alliance_members import get_current_user_id


def test_get_current_user_id_raises():
    with pytest.raises(HTTPException):
        get_current_user_id(None)


def test_transfer_leadership_changes_leader():
    Session = setup_db()
    db = Session()
    db.add(Alliance(alliance_id=1, name="Test", leader="u1"))
    db.add(AllianceMember(alliance_id=1, user_id="u1", username="A", rank="Leader"))
    db.add(AllianceMember(alliance_id=1, user_id="u2", username="B", rank="Member"))
    db.commit()

    transfer_leadership(TransferLeadershipPayload(new_leader_id="u2"), user_id="u1", db=db)
    alliance = db.query(Alliance).filter_by(alliance_id=1).first()
    assert alliance.leader == "u2"
    m1 = db.query(AllianceMember).filter_by(user_id="u1").first()
    m2 = db.query(AllianceMember).filter_by(user_id="u2").first()
    assert m1.rank == "Co-Leader"
    assert m2.rank == "Leader"
