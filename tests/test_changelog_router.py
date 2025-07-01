# Comment
# Project Name: Thronestead©
# File Name: test_changelog_router.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
from backend.routers import system_changelog


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []

    def select(self, *args):
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, *args):
        return self

    def execute(self):
        return {"data": self._data}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_returns_sorted_entries():
    entries = [
        {"version": "1.0.0", "release_date": "2025-01-01", "changes": ["init"]},
        {"version": "1.1.0", "release_date": "2025-02-01", "changes": ["new"]},
    ]
    for row in entries:
        row["title"] = "t"
    client = DummyClient({"game_changelog": entries})
    system_changelog.get_supabase_client = lambda: client
    result = system_changelog.get_system_changelog()
    assert result[0]["version"] == "1.1.0"
    assert result[0]["title"] == "t"
    assert len(result) == 2
