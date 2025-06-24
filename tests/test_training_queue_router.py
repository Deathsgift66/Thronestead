# Project Name: Thronestead©
# File Name: test_training_queue_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from backend.routers.training_queue import (
    CancelPayload,
    TrainOrderPayload,
    begin_order,
    cancel_order,
    list_queue,
    pause_order,
    start_training,
)


class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows

    def scalar(self):
        return self._row[0] if self._row else None


class DummyDB:
    def __init__(self):
        self.executed = []
        self.rows = []

    def execute(self, query, params=None):
        q = str(query)
        self.executed.append((q, params))
        if "FROM kingdoms" in q:
            return DummyResult((1,))
        if q.strip().startswith("INSERT INTO training_queue"):
            return DummyResult((5,))
        if q.strip().startswith("UPDATE training_queue"):
            return DummyResult()
        if "FROM training_queue" in q:
            return DummyResult(rows=self.rows)
        return DummyResult()

    def commit(self):
        pass


def test_start_training_returns_id():
    db = DummyDB()
    payload = TrainOrderPayload(
        unit_id=2, unit_name="Archer", quantity=5, base_training_seconds=60
    )
    res = start_training(payload, user_id="u1", db=db)
    assert res["queue_id"] == 5


def test_list_queue_returns_rows():
    db = DummyDB()
    db.rows = [(1, "Knight", 10, "2025-06-10", "queued")]
    res = list_queue(user_id="u1", db=db)
    assert len(res["queue"]) == 1
    assert res["queue"][0]["unit_name"] == "Knight"


def test_cancel_order_updates_row():
    db = DummyDB()
    cancel_order(CancelPayload(queue_id=2), user_id="u1", db=db)
    executed = " ".join(db.executed[-1][0].split()).lower()
    assert "update training_queue" in executed


def test_begin_order_updates_status():
    db = DummyDB()
    begin_order(CancelPayload(queue_id=3), user_id="u1", db=db)
    executed = db.executed[-1][0].lower()
    assert "training'" in executed


def test_pause_order_updates_status():
    db = DummyDB()
    pause_order(CancelPayload(queue_id=4), user_id="u1", db=db)
    executed = db.executed[-1][0].lower()
    assert "paused" in executed
