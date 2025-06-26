# Project Name: Thronestead©
# File Name: test_profile_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import HTTPException

from backend.routers import profile_view


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []
        self._single = False

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._single:
            return {"data": self._data[0] if self._data else None}
        return {"data": self._data}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_profile_overview_returns_data():
    tables = {
        "users": [
            {
                "user_id": "u1",
                "username": "Hero",
                "kingdom_name": "Realm",
                "profile_bio": "bio",
                "profile_picture_url": "pic.png",
                "last_login_at": "2025-01-01T00:00:00Z",
            }
        ],
        "player_messages": [
            {"message_id": 1, "recipient_id": "u1", "is_read": False},
            {"message_id": 2, "recipient_id": "u1", "is_read": False},
        ],
    }
    profile_view.get_supabase_client = lambda: DummyClient(tables)
    result = profile_view.profile_overview(user_id="u1")
    assert result["user"]["username"] == "Hero"
    assert result["unread_messages"] == 2
    assert result["user"]["last_login_at"] == "2025-01-01T00:00:00Z"


def test_profile_overview_missing_user():
    profile_view.get_supabase_client = lambda: DummyClient({"users": []})
    try:
        profile_view.profile_overview(user_id="x")
    except HTTPException as e:
        assert e.status_code == 404
    else:
        assert False
