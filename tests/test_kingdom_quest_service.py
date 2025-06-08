from datetime import datetime

from services.kingdom_quest_service import (
    start_quest,
    update_progress,
    complete_quest,
    cancel_quest,
)


class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []
        self.rowcount = 0

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.queries = []
        self.row = (1,)
        self.commits = 0

    def execute(self, query, params=None):
        q = str(query).strip()
        self.queries.append((q, params))
        if q.startswith("SELECT duration_hours"):
            return DummyResult(row=self.row)
        return DummyResult()

    def commit(self):
        self.commits += 1


def test_start_quest_inserts():
    db = DummyDB()
    ends_at = start_quest(db, 1, "demo", "u1")
    assert any("INSERT INTO quest_kingdom_tracking" in q for q, _ in db.queries)
    assert isinstance(ends_at, datetime)
    assert db.commits == 1


def test_update_and_complete():
    db = DummyDB()
    update_progress(db, 1, "demo", 50, {"g": 1})
    assert any("UPDATE quest_kingdom_tracking" in q for q, _ in db.queries)
    complete_quest(db, 1, "demo")
    assert any("status='completed'" in q for q, _ in db.queries)
    cancel_quest(db, 1, "demo")
    assert any("status='cancelled'" in q for q, _ in db.queries)
    assert db.commits == 3

