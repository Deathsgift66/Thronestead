from fastapi import HTTPException

from services.village_queue_service import (
    queue_building_upgrade,
    start_next_in_queue,
    mark_completed_queued_buildings,
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
        self.row = None
        self.rows = []

    def execute(self, query, params=None):
        self.executed.append(str(query))
        q = str(query).lower()
        if "insert into village_queue" in q:
            return DummyResult((1,))
        if "select level from village_buildings" in q:
            return DummyResult((1,))
        if "select queue_id, building_type" in q and "status = 'pending'" in q:
            return DummyResult((1, 'farm', 2))
        if "select build_time_seconds" in q:
            return DummyResult((60,))
        if "select queue_id, village_id" in q and "status = 'in_progress'" in q:
            return DummyResult(rows=self.rows)
        return DummyResult()

    def commit(self):
        pass


def test_queue_building_upgrade_inserts():
    db = DummyDB()
    queue_id = queue_building_upgrade(db, 1, 'farm')
    assert queue_id == 1
    assert any("insert into village_queue" in q.lower() for q in db.executed)


def test_start_next_in_queue_updates():
    db = DummyDB()
    start_next_in_queue(db, 1)
    assert any("update village_queue" in q.lower() for q in db.executed)


def test_mark_completed_processes_rows():
    db = DummyDB()
    db.rows = [(1, 1, 'farm', 2)]
    processed = mark_completed_queued_buildings(db)
    assert processed == 1
    joined = " ".join(db.executed).lower()
    assert "update village_queue" in joined
    assert "insert into village_buildings" in joined
