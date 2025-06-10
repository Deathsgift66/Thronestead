from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import (
    Alliance,
    User,
    QuestAllianceCatalogue,
    QuestAllianceTracking,
    QuestAllianceContribution,
)
from backend.routers import alliance_quests


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db, alliance_id=1, role="Leader"):
    uid = "00000000-0000-0000-0000-000000000001"
    user = User(
        user_id=uid,
        username="tester",
        display_name="Tester",
        email="t@example.com",
        alliance_id=alliance_id,
        alliance_role=role,
    )
    db.add(user)
    db.add(Alliance(alliance_id=alliance_id, name="A"))
    db.commit()
    return uid


def test_catalogue_returns_active():
    Session = setup_db()
    db = Session()
    db.add(QuestAllianceCatalogue(quest_code="q1", name="One", is_active=True))
    db.add(QuestAllianceCatalogue(quest_code="q2", name="Two", is_active=False))
    db.commit()

    res = alliance_quests.get_quest_catalogue(db=db)
    assert len(res) == 1
    assert res[0]["quest_code"] == "q1"


def test_available_excludes_started():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    db.add(QuestAllianceCatalogue(quest_code="q1", name="One", is_active=True))
    db.add(QuestAllianceCatalogue(quest_code="q2", name="Two", is_active=True))
    db.add(
        QuestAllianceTracking(
            alliance_id=1,
            quest_code="q1",
            status="active",
            progress=0,
        )
    )
    db.commit()

    res = alliance_quests.get_available_quests(user_id=uid, db=db)
    codes = {q["quest_code"] for q in res}
    assert codes == {"q2"}


def test_start_quest_creates_tracking():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    db.add(
        QuestAllianceCatalogue(
            quest_code="q1",
            name="One",
            is_active=True,
            duration_hours=1,
        )
    )
    db.commit()

    res = alliance_quests.start_quest(
        alliance_quests.QuestStartPayload(quest_code="q1"),
        user_id=uid,
        db=db,
    )
    row = (
        db.query(QuestAllianceTracking)
        .filter_by(alliance_id=1, quest_code="q1")
        .first()
    )
    assert row is not None and row.status == "active"
    assert res["status"] == "started"


def test_detail_returns_tracking_and_contributions():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    db.add(
        QuestAllianceCatalogue(
            quest_code="q1",
            name="One",
            description="D",
            is_active=True,
        )
    )
    db.add(
        QuestAllianceTracking(
            alliance_id=1,
            quest_code="q1",
            status="active",
            progress=25,
        )
    )
    db.add(
        QuestAllianceContribution(
            alliance_id=1,
            player_name="Tester",
            resource_type="gold",
            amount=10,
            quest_code="q1",
            user_id=uid,
        )
    )
    db.commit()

    res = alliance_quests.quest_detail("q1", user_id=uid, db=db)
    assert res["quest_code"] == "q1"
    assert res["progress"] == 25
    assert len(res["contributions"]) == 1


def test_progress_marks_completed_and_chains():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    db.add(
        QuestAllianceCatalogue(
            quest_code="q1",
            name="One",
            is_active=True,
            rewards={"unlock_next": "q2"},
        )
    )
    db.add(QuestAllianceCatalogue(quest_code="q2", name="Two", is_active=True))
    db.add(
        QuestAllianceTracking(
            alliance_id=1,
            quest_code="q1",
            status="active",
            progress=90,
        )
    )
    db.commit()

    alliance_quests.update_progress(
        alliance_quests.ProgressPayload(quest_code="q1", amount=15),
        user_id=uid,
        db=db,
    )
    row = (
        db.query(QuestAllianceTracking)
        .filter_by(alliance_id=1, quest_code="q1")
        .first()
    )
    assert row.status == "completed" and row.progress == 100
    chained = (
        db.query(QuestAllianceTracking)
        .filter_by(alliance_id=1, quest_code="q2")
        .first()
    )
    assert chained is not None and chained.status == "active"


def test_claim_reward_sets_flag():
    Session = setup_db()
    db = Session()
    uid = create_user(db)
    db.add(
        QuestAllianceCatalogue(quest_code="q3", name="Three", is_active=True)
    )
    db.add(
        QuestAllianceTracking(
            alliance_id=1,
            quest_code="q3",
            status="completed",
            progress=100,
        )
    )
    db.commit()

    alliance_quests.claim_reward(
        alliance_quests.ClaimPayload(quest_code="q3"),
        user_id=uid,
        db=db,
    )
    row = (
        db.query(QuestAllianceTracking)
        .filter_by(alliance_id=1, quest_code="q3")
        .first()
    )
    assert row.reward_claimed is True
