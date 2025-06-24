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
    finalize_completed_orders,
)
import services.training_queue_service as training_queue_service
import services.training_history_service as training_history_service


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
        self.troop_row = (10, 0, 1)

    def execute(self, query, params=None):
        q = str(query).lower()
        self.executed.append((q, params))
        if q.strip().startswith("insert into training_queue"):
            return DummyResult((1,))
        if "from training_queue" in q:
            return DummyResult(rows=self.rows)
        if q.strip().startswith("insert into training_history"):
            return DummyResult((1,))
        if "select quantity, unit_xp, unit_level from kingdom_troops" in q:
            return DummyResult(row=self.troop_row)
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
        training_speed_multiplier=2.0,
        xp_per_unit=5,
        modifiers_applied=None,
        initiated_by="u1",
        priority=1,
    )
    assert qid == 1
    assert len(db.executed) == 1
    query = db.executed[0][0]
    assert "INSERT INTO training_queue" in query
    assert ":base * :qty * :speed" in query


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
    db.rows = [(
        1,
        5,
        "Knight",
        10,
        "2025-06-09",
        "u1",
        {},
        5,
        2.0,
    )]
    cancel_training(db, 2, 1)
    mark_completed(db, 3)
    queries = " ".join(q for q, _ in db.executed)

    assert "update training_queue" in queries
    assert "insert into training_history" in queries




def test_begin_and_pause():
    db = DummyDB()
    begin_training(db, 4, 1)
    pause_training(db, 4, 1)
    assert "training'" in db.executed[-2][0]
    assert "paused" in db.executed[-1][0]

def test_finalize_completed_orders(monkeypatch):
    db = DummyDB()
    db.rows = [
        (
            1,
            1,
            2,
            "Knight",
            5,
            "2025-06-10",
            "u1",
            {},
            3,
        )
    ]

    called = {}

    def fake_mark(db_arg, qid):
        called.setdefault("mark", []).append(qid)

    def fake_record(
        db_arg,
        kingdom_id,
        unit_id,
        unit_name,
        quantity,
        source,
        initiated_at,
        trained_by,
        modifiers_applied,
        xp_per_unit=0,
    ):
        called["record"] = xp_per_unit

    monkeypatch.setattr(training_queue_service, "mark_completed", fake_mark)
    monkeypatch.setattr(training_history_service, "record_training", fake_record)

    processed = training_queue_service.finalize_completed_orders(db)
    assert processed == 1
    assert called["mark"] == [1]
    assert called["record"] == 3
    assert any("DELETE FROM training_queue" in q for q, _ in db.executed)

