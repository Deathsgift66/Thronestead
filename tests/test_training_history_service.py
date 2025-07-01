# Comment
# Project Name: Thronestead©
# File Name: test_training_history_service.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
from services.training_history_service import fetch_history, record_training
from services.unit_xp_service import level_up_units


class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self, troop_row=None):
        self.executed = []
        self.rows = []
        self.troop_row = troop_row

    def execute(self, query, params=None):
        q = str(query).lower()
        self.executed.append((q, params))
        if q.strip().startswith("insert into training_history"):
            return DummyResult((1,))
        if "from training_history" in q:
            return DummyResult(rows=self.rows)
        if "select quantity, unit_xp, unit_level from kingdom_troops" in q:
            return DummyResult(row=self.troop_row)
        return DummyResult()

    def commit(self):
        pass


def test_record_training_inserts():
    db = DummyDB(troop_row=(10, 0, 1))
    hid = record_training(
        db,
        kingdom_id=1,
        unit_id=5,
        unit_name="Knight",
        quantity=10,
        source="manual",
        initiated_at="2025-06-09 10:00",
        trained_by="u1",
        modifiers_applied={"bonus": 10},
        xp_per_unit=5,
        speed_modifier=2.0,
    )
    assert hid == 1
    joined = " ".join(q for q, _ in db.executed)
    assert "insert into training_history" in joined
    assert "xp_awarded" in joined
    assert "insert into kingdom_troops" in joined


def test_fetch_history_returns_rows():
    db = DummyDB()
    db.rows = [("Knight", 10, "2025-06-10", "manual")]
    rows = fetch_history(db, 1, 20)
    assert len(rows) == 1
    assert rows[0]["unit_name"] == "Knight"


def test_level_up_units_moves_quantity():
    db = DummyDB(troop_row=(5, 120, 1))
    level_up_units(db, 1, "Knight")
    joined = " ".join(q for q, _ in db.executed)
    assert "update kingdom_troops" in joined
    assert joined.count("insert into kingdom_troops") >= 1
