from fastapi import HTTPException

from services.kingdom_building_service import upgrade_building


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self):
        self.queries = []
        self.params = []
        self.row_sequence = []
        self.committed = False

    def execute(self, query, params=None):
        self.queries.append(str(query))
        self.params.append(params)
        row = None
        if self.row_sequence:
            row = self.row_sequence.pop(0)
        return DummyResult(row)

    def commit(self):
        self.committed = True


def test_upgrade_building_at_max_level_raises():
    db = DummyDB()
    db.row_sequence = [(1, 3), (3,)]  # current level 3, max_level 3
    try:
        upgrade_building(db, 1, 1, "u1", 60)
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        assert False, "Expected HTTPException"
    assert not any("UPDATE village_buildings" in q for q in db.queries)


def test_upgrade_building_success():
    db = DummyDB()
    db.row_sequence = [(1, 2), (3,)]  # current level 2, max_level 3
    upgrade_building(db, 1, 1, "u1", 60)
    assert any("UPDATE village_buildings" in q for q in db.queries)
    assert db.committed
