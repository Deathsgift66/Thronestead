from backend.routers.battle import get_battle_history


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self, rows=None):
        self.rows = rows or []

    def execute(self, query, params=None):
        return DummyResult(self.rows)


def test_get_battle_history_returns_rows():
    db = DummyDB([
        (
            1,
            "A",
            "B",
            "attacker",
            10,
            5,
            "2025-01-01",
        )
    ])
    result = get_battle_history(kingdom_id=1, limit=10, db=db, user_id="u1")
    assert len(result["history"]) == 1
    assert result["history"][0]["war_id"] == 1

