from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import AllianceMember, User
from backend.routers.alliance_members import promote, RankPayload


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_promote_updates_rank():
    Session = setup_db()
    db = Session()
    db.add(AllianceMember(alliance_id=1, user_id="u1", username="A", rank="Member"))
    db.add(User(user_id="admin", username="admin", email="a@example.com", alliance_id=1, alliance_role="Leader"))
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
