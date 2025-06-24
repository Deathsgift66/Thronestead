from services.unit_xp_service import award_unit_xp, level_up_units


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
        self.troop_row = troop_row

    def execute(self, query, params=None):
        q = str(query).lower()
        self.executed.append((q, params))
        if "select quantity, unit_xp, unit_level from kingdom_troops" in q:
            return DummyResult(row=self.troop_row)
        return DummyResult()

    def commit(self):
        pass


def test_award_unit_xp_inserts():
    db = DummyDB(troop_row=(10, 0, 1))
    award_unit_xp(db, 1, "Knight", 50, quantity=5)
    joined = " ".join(q for q, _ in db.executed)
    assert "insert into kingdom_troops" in joined


def test_level_up_units_promotes_units():
    db = DummyDB(troop_row=(5, 120, 1))
    level_up_units(db, 1, "Knight")
    joined = " ".join(q for q, _ in db.executed)
    assert "update kingdom_troops" in joined
    assert joined.count("insert into kingdom_troops") >= 1
