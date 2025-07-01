# Project Name: Thronestead©
# File Name: test_alliance_members_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Alliance, AllianceMember, User
from backend.routers.alliance_members import (
    RankPayload,
    TransferLeadershipPayload,
    promote,
    transfer_leadership,
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
    db.add(
        User(
            user_id="admin",
            username="Admin",
            email="a@test.com",
            alliance_id=1,
            alliance_role="Leader",
        )
    )
    db.commit()

    promote(
        RankPayload(user_id="u1", alliance_id=1, new_rank="Leader"),
        user_id="admin",
        db=db,
    )
    row = db.query(AllianceMember).filter_by(user_id="u1").first()
    assert row.rank == "Leader"


def test_transfer_leadership_changes_leader():
    Session = setup_db()
    db = Session()
    db.add(Alliance(alliance_id=1, name="Test", leader="u1"))
    db.add(AllianceMember(alliance_id=1, user_id="u1", username="A", rank="Leader"))
    db.add(AllianceMember(alliance_id=1, user_id="u2", username="B", rank="Member"))
    db.commit()

    transfer_leadership(
        TransferLeadershipPayload(new_leader_id="u2"), user_id="u1", db=db
    )
    alliance = db.query(Alliance).filter_by(alliance_id=1).first()
    assert alliance.leader == "u2"
    m1 = db.query(AllianceMember).filter_by(user_id="u1").first()
    m2 = db.query(AllianceMember).filter_by(user_id="u2").first()
    assert m1.rank == "Co-Leader"
    assert m2.rank == "Leader"
