from backend.routers.training_queue import start_training, list_queue, TrainOrderPayload

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
        if "FROM training_queue" in q:
            return DummyResult(rows=self.rows)
        return DummyResult()
    def commit(self):
        pass


def test_start_training_returns_id():
    db = DummyDB()
    payload = TrainOrderPayload(unit_id=2, unit_name="Archer", quantity=5, base_training_seconds=60)
    res = start_training(payload, user_id="u1", db=db)
    assert res["queue_id"] == 5


def test_list_queue_returns_rows():
    db = DummyDB()
    db.rows = [(1, "Knight", 10, "2025-06-10", "queued")]
    res = list_queue(user_id="u1", db=db)
    assert len(res["queue"]) == 1
    assert res["queue"][0]["unit_name"] == "Knight"

