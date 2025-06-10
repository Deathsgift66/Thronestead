from fastapi import HTTPException
from backend.routers import navbar


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


def test_navbar_profile_returns_data():
    tables = {
        "users": [
            {"user_id": "u1", "username": "Hero", "profile_picture_url": "pic.png"}
        ],
        "player_messages": [
            {"message_id": 1, "recipient_id": "u1", "is_read": False}
        ],
    }
    navbar.get_supabase_client = lambda: DummyClient(tables)
    result = navbar.navbar_profile(user_id="u1")
    assert result["username"] == "Hero"
    assert result["unread_messages"] == 1


def test_navbar_profile_missing_user():
    navbar.get_supabase_client = lambda: DummyClient({"users": []})
    try:
        navbar.navbar_profile(user_id="u1")
    except HTTPException as e:
        assert e.status_code == 404
    else:
        assert False
