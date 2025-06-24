# Project Name: Thronestead©
# File Name: test_training_queue_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from services.training_queue_service import (
    add_training_order,
    begin_training,
    cancel_training,
    fetch_queue,
    pause_training,
    mark_completed,
)


class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.executed = []
        self.rows = []

    def execute(self, query, params=None):
        q = str(query)
        self.executed.append((q, params))
        if q.strip().startswith("INSERT INTO training_queue"):
            return DummyResult((1,))
        if "FROM training_queue" in q:
            return DummyResult(rows=self.rows)
        return DummyResult()

    def commit(self):
        pass


def test_add_training_order_inserts():
    db = DummyDB()
    qid = add_training_order(
        db,
        kingdom_id=1,
        unit_id=5,
        unit_name="Knight",
        quantity=10,
        base_training_seconds=60,
        training_speed_modifier=1.0,
        modifiers_applied=None,
        initiated_by="u1",
        priority=1,
    )
    assert qid == 1
    assert len(db.executed) == 1
    assert "INSERT INTO training_queue" in db.executed[0][0]


def test_fetch_queue_returns_rows():
    db = DummyDB()
    db.rows = [(1, "Knight", 10, "2025-06-10", "queued", False, False)]
    rows = fetch_queue(db, 1)
    assert len(rows) == 1
    assert rows[0]["unit_name"] == "Knight"
    assert rows[0]["is_support"] is False
    assert rows[0]["is_siege"] is False


def test_cancel_and_complete():
    db = DummyDB()
    cancel_training(db, 2, 1)
    mark_completed(db, 3)
    queries = " ".join(q for q, _ in db.executed)
    assert "UPDATE training_queue" in queries


def test_begin_and_pause():
    db = DummyDB()
    begin_training(db, 4, 1)
    pause_training(db, 4, 1)
    assert "training'" in db.executed[-2][0]
    assert "paused" in db.executed[-1][0]
