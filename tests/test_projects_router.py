# Project Name: Thronestead©
# File Name: test_projects_router.py
# Version: 7/1/2025 10:38
# Developer: Deathsgift66
"""Tests for the kingdom projects router."""

import pytest
from fastapi import HTTPException

from backend.routers import projects_router as pr
from backend.data import kingdom_projects, castle_progression_state


class DummyDB:
    """Placeholder DB object used for dependency injection."""
    pass


def test_start_project_records_entry(monkeypatch):
    kingdom_projects.clear()
    castle_progression_state[1] = {"castle_level": 5, "nobles": 2, "knights": 1}

    called = {}

    def fake_check(db, kid):
        called["kid"] = kid

    monkeypatch.setattr(pr, "check_vacation_mode", fake_check)

    payload = pr.ProjectPayload(project_code="barracks_upgrade")
    res = pr.start_project(payload, user_id="u1", db=DummyDB())

    assert called.get("kid") == 1
    assert res["project_code"] == "barracks_upgrade"
    assert len(kingdom_projects[1]) == 1


def test_start_project_rejects_unmet_requirements(monkeypatch):
    kingdom_projects.clear()
    castle_progression_state[1] = {"castle_level": 1, "nobles": 0, "knights": 0}
    monkeypatch.setattr(pr, "check_vacation_mode", lambda *_: None)

    with pytest.raises(HTTPException):
        pr.start_project(
            pr.ProjectPayload(project_code="barracks_upgrade"),
            user_id="u2",
            db=DummyDB(),
        )


def test_project_status_returns_projects(monkeypatch):
    kingdom_projects.clear()
    kingdom_projects[1] = [{"project_code": "demo_project"}]

    res = pr.project_status(1, user_id="u1")
    assert res["projects"][0]["project_code"] == "demo_project"
