# Comment
# Project Name: Thronestead©
# File Name: test_quests_router.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import Kingdom, QuestKingdomTracking, User
from backend.routers.quests_router import get_active_quests


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_kingdom_user(db):
    uid = "00000000-0000-0000-0000-000000000001"
    user = User(user_id=uid, username="t", display_name="t", email="e@example.com")
    db.add(user)
    db.add(Kingdom(kingdom_id=1, user_id=uid, kingdom_name="K"))
    db.add(
        QuestKingdomTracking(
            kingdom_id=1, quest_code="q1", status="active", progress=10
        )
    )
    db.commit()
    return uid


def test_active_quests_returns_rows():
    Session = setup_db()
    db = Session()
    uid = create_kingdom_user(db)
    rows = get_active_quests(user_id=uid, db=db)
    assert len(rows) == 1
    assert rows[0]["quest_code"] == "q1"
