# Project Name: Thronestead©
# File Name: test_vip_leaderboard_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from backend.routers import donate_vip


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []
        self._ordered = self._data

    def select(self, *_args):
        return self

    def order(self, column, desc=True):
        self._ordered = sorted(self._data, key=lambda x: x[column], reverse=desc)
        return self

    def limit(self, n):
        self._ordered = self._ordered[:n]
        return self

    def execute(self):
        return {"data": self._ordered}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        return DummyTable(self.tables.get(name, []))


def test_vip_leaderboard_sorted():
    data = [
        {"user_id": "u1", "username": "A", "total_donated": 100},
        {"user_id": "u2", "username": "B", "total_donated": 200},
    ]
    donate_vip.get_supabase_client = lambda: DummyClient({"vip_donations": data})
    result = donate_vip.vip_leaderboard(user_id="u1")
    assert result["leaders"][0]["total_donated"] == 200
    assert len(result["leaders"]) == 2
