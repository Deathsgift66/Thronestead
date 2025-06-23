# Project Name: Thronestead©
# File Name: test_alliance_changelog_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from backend.routers import alliance_changelog as ac
from fastapi import HTTPException


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def single(self):
        self._single = True
        return self

    def or_(self, *_args):
        return self

    def in_(self, *_args):
        return self

    def execute(self):
        if self._single:
            if self._data:
                return {"data": self._data[0]}
            return {"data": None}
        return {"data": self._data}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_invalid_user():
    client = DummyClient({"users": []})
    ac.get_supabase_client = lambda: client
    try:
        ac.get_alliance_changelog(user_id="u1")
    except HTTPException as e:
        assert e.status_code == 401
    else:
        assert False


def test_returns_sorted_list():
    logs = [
        {"created_at": "2025-01-02T12:00:00", "user_id": "u1", "description": "late"},
        {"created_at": "2025-01-01T12:00:00", "user_id": "u1", "description": "early"},
    ]
    tables = {
        "users": [{"user_id": "u1"}],
        "alliance_members": [{"alliance_id": 1}],
        "alliance_activity_log": logs,
        "alliance_treaties": [],
        "alliance_wars": [],
        "projects_alliance": [],
        "quest_alliance_tracking": [],
        "audit_log": [],
    }
    client = DummyClient(tables)
    ac.get_supabase_client = lambda: client
    result = ac.get_alliance_changelog(user_id="u1")
    assert result["logs"][0]["description"] == "late"
    assert len(result["logs"]) == 2
    assert "last_updated" in result


def test_filters_applied():
    logs = [
        {
            "created_at": "2025-01-02T12:00:00",
            "user_id": "u1",
            "description": "war log",
            "event_type": "war",
        },
        {
            "created_at": "2025-01-03T12:00:00",
            "user_id": "u1",
            "description": "quest log",
            "event_type": "quest",
        },
    ]
    tables = {
        "users": [{"user_id": "u1"}],
        "alliance_members": [{"alliance_id": 1}],
        "alliance_activity_log": [],
        "alliance_treaties": [],
        "alliance_wars": [logs[0]],
        "projects_alliance": [],
        "quest_alliance_tracking": [logs[1]],
        "audit_log": [],
    }
    client = DummyClient(tables)
    ac.get_supabase_client = lambda: client
    res = ac.get_alliance_changelog(
        start="2025-01-03T00:00:00", event_type="quest", user_id="u1"
    )
    assert len(res["logs"]) == 1
    assert res["logs"][0]["description"] == "quest log"
