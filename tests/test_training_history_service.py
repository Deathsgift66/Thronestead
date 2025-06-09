from services.training_history_service import record_training, fetch_history


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
        if q.strip().startswith("INSERT INTO training_history"):
            return DummyResult((1,))
        if "FROM training_history" in q:
            return DummyResult(rows=self.rows)
        return DummyResult()

    def commit(self):
        pass


def test_record_training_inserts():
    db = DummyDB()
    hid = record_training(
        db,
        kingdom_id=1,
        unit_id=5,
        unit_name="Knight",
        quantity=10,
        source="manual",
        initiated_at="2025-06-09 10:00",
        trained_by="u1",
        xp_awarded=50,
        modifiers_applied={"bonus": 10},
    )
    assert hid == 1
    assert len(db.executed) == 1
    assert "INSERT INTO training_history" in db.executed[0][0]


def test_fetch_history_returns_rows():
    db = DummyDB()
    db.rows = [("Knight", 10, "2025-06-10", "manual", 50)]
    rows = fetch_history(db, 1, 20)
    assert len(rows) == 1
    assert rows[0]["unit_name"] == "Knight"
