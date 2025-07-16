# Project Name: Thronestead©
# File Name: test_alliance_projects_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from datetime import datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import (
    Alliance,
    AllianceMember,
    AllianceRole,
    ProjectAllianceCatalogue,
    ProjectAllianceContribution,
    ProjectsAlliance,
    ProjectsAllianceInProgress,
    User,
)
from backend.routers.alliance_projects import (
    ContributionPayload,
    StartPayload,
    contribute_to_project,
    get_available_projects,
    get_in_progress_projects,
    start_alliance_project,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def seed_basic(db, perms=("can_manage_projects",)):
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

    role = AllianceRole(role_id=1, alliance_id=1, role_name="Leader", permissions=list(perms))
    db.add(role)
    db.add(AllianceMember(alliance_id=1, user_id=user.user_id, username="tester", role_id=1))
    db.commit()
    return user.user_id


def test_available_excludes_existing():
    Session = setup_db()
    db = Session()
    uid = seed_basic(db)
    db.add(
        ProjectAllianceCatalogue(
            project_key="p1", project_name="One", requires_alliance_level=1
        )
    )
    db.add(
        ProjectAllianceCatalogue(
            project_key="p2", project_name="Two", requires_alliance_level=2
        )
    )
    db.add(
        ProjectsAlliance(
            alliance_id=1, name="Built", project_key="p1", build_state="completed"
        )
    )
    db.add(ProjectsAllianceInProgress(alliance_id=1, project_key="p2", progress=10))
    db.commit()

    res = get_available_projects(1, uid, db)
    assert res["projects"] == []


def test_start_creates_progress_row():
    Session = setup_db()
    db = Session()
    uid = seed_basic(db)
    db.add(
        ProjectAllianceCatalogue(
            project_key="p3", project_name="Three", build_time_seconds=10
        )
    )
    db.commit()

    start_alliance_project(StartPayload(project_key="p3", user_id=uid), uid, db)
    rows = get_in_progress_projects(1, uid, db)
    assert len(rows["projects"]) == 1
    assert rows["projects"][0]["project_key"] == "p3"


def test_start_rejects_if_active():
    Session = setup_db()
    db = Session()
    uid = seed_basic(db)
    db.add(ProjectAllianceCatalogue(project_key="p4", project_name="Four"))
    db.add(ProjectAllianceCatalogue(project_key="p5", project_name="Five"))
    db.add(
        ProjectsAllianceInProgress(
            alliance_id=1,
            project_key="p4",
            progress=0,
            status="building",
            expected_end=datetime.utcnow(),
        )
    )
    db.commit()
    with pytest.raises(HTTPException):
        start_alliance_project(StartPayload(project_key="p5", user_id=uid), uid, db)


def test_start_requires_permission():
    Session = setup_db()
    db = Session()
    uid = seed_basic(db, perms=())
    db.add(ProjectAllianceCatalogue(project_key="p9", project_name="Nine"))
    db.commit()
    with pytest.raises(HTTPException):
        start_alliance_project(StartPayload(project_key="p9", user_id=uid), uid, db)


def test_contribute_records_entry():
    Session = setup_db()
    db = Session()
    uid = seed_basic(db)
    db.add(ProjectAllianceCatalogue(project_key="p6", project_name="Six"))
    db.add(
        ProjectsAllianceInProgress(
            alliance_id=1,
            project_key="p6",
            progress=0,
            status="building",
            expected_end=datetime.utcnow(),
        )
    )
    db.commit()

    contribute_to_project(
        ContributionPayload(
            project_key="p6", resource_type="wood", amount=5, user_id=uid
        ),
        uid,
        db,
    )
    rows = db.query(ProjectAllianceContribution).filter_by(project_key="p6").all()
    assert len(rows) == 1 and rows[0].amount == 5
