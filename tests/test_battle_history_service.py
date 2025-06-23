from services.battle_history_service import fetch_history


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.rows = []
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((str(query), params))
        return DummyResult(self.rows)


def test_fetch_history_returns_rows():
    db = DummyDB()
    db.rows = [(
        1,
        "A",
        "B",
        "attacker",
        10,
        5,
        "2025-01-01",
    )]
    res = fetch_history(db, 1, 10)
    assert len(res) == 1
    assert res[0]["war_id"] == 1

