from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pytest

from fastapi import HTTPException
from backend.database import Base
from backend.models import (
    Alliance,
    ProjectAllianceCatalogue,
    ProjectsAlliance,
    ProjectsAllianceInProgress,
    ProjectAllianceContribution,
    User,
)
from backend.routers.alliance_projects import (
    get_available_projects,
    start_alliance_project,
    contribute_to_project,
    project_leaderboard,
    StartPayload,
    ContributionPayload,
    get_in_progress_projects,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_basic(db):
    user = User(
        user_id="00000000-0000-0000-0000-000000000001",
        username="tester",
        display_name="Tester",
        email="t@example.com",
        alliance_id=1,
    )
    db.add(user)
    alliance = Alliance(alliance_id=1, name="A", level=3)
    db.add(alliance)
    db.commit()
    return user.user_id


def test_available_excludes_existing():
    Session = setup_db()
    db = Session()
    uid = seed_basic(db)
    db.add(ProjectAllianceCatalogue(project_code="p1", project_name="One", requires_alliance_level=1))
    db.add(ProjectAllianceCatalogue(project_code="p2", project_name="Two", requires_alliance_level=2))
    db.add(ProjectsAlliance(alliance_id=1, name="Built", project_key="p1", build_state="completed"))
    db.add(ProjectsAllianceInProgress(alliance_id=1, project_key="p2", progress=10))
    db.commit()

    res = get_available_projects(1, uid, db)
    assert res["projects"] == []


def test_start_creates_progress_row():
    Session = setup_db()
    db = Session()
    uid = seed_basic(db)
    db.add(ProjectAllianceCatalogue(project_code="p3", project_name="Three", build_time_seconds=10))
    db.commit()

    start_alliance_project(StartPayload(project_key="p3", user_id=uid), uid, db)
    rows = get_in_progress_projects(1, uid, db)
    assert len(rows["projects"]) == 1
    assert rows["projects"][0]["project_key"] == "p3"


def test_start_rejects_if_active():
    Session = setup_db()
    db = Session()
    uid = seed_basic(db)
    db.add(ProjectAllianceCatalogue(project_code="p4", project_name="Four"))
    db.add(ProjectAllianceCatalogue(project_code="p5", project_name="Five"))
    db.add(ProjectsAllianceInProgress(alliance_id=1, project_key="p4", progress=0, status="building", expected_end=datetime.utcnow()))
    db.commit()
    with pytest.raises(HTTPException):
        start_alliance_project(StartPayload(project_key="p5", user_id=uid), uid, db)


def test_contribute_records_entry():
    Session = setup_db()
    db = Session()
    uid = seed_basic(db)
    db.add(ProjectAllianceCatalogue(project_code="p6", project_name="Six"))
    db.add(ProjectsAllianceInProgress(alliance_id=1, project_key="p6", progress=0, status="building", expected_end=datetime.utcnow()))
    db.commit()

    contribute_to_project(
        ContributionPayload(project_key="p6", resource_type="wood", amount=5, user_id=uid),
        uid,
        db,
    )
    rows = db.query(ProjectAllianceContribution).filter_by(project_key="p6").all()
    assert len(rows) == 1 and rows[0].amount == 5
