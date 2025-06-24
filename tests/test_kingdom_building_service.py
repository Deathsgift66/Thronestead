from fastapi import HTTPException
import pytest

from services.kingdom_building_service import upgrade_building
import services.kingdom_building_service as building_service


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
    db.row_sequence = [(1, 3), {"max_level": 3}]  # current level 3, max_level 3
    try:
        upgrade_building(db, 1, 1, "u1", 60)
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        assert False, "Expected HTTPException"
    assert not any("UPDATE village_buildings" in q for q in db.queries)


def test_upgrade_building_success():
    db = DummyDB()
    db.row_sequence = [
        (1, 2),
        {"max_level": 3, "wood": 5},
        (1,),
    ]  # current level 2, max_level 3
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(
        building_service.resource_service,
        "spend_resources",
        lambda *_a, **_k: None,
    )
    upgrade_building(db, 1, 1, "u1", 60)
    monkeypatch.undo()
    assert any("UPDATE village_buildings" in q for q in db.queries)
    assert db.committed


def test_upgrade_building_spends_resources(monkeypatch):
    db = DummyDB()
    db.row_sequence = [
        (1, 1),
        {"max_level": 5, "wood": 10},
        (2,),
    ]
    called = {}
    monkeypatch.setattr(
        building_service.resource_service,
        "spend_resources",
        lambda *_a, **_k: called.setdefault("spent", True),
    )
    upgrade_building(db, 1, 1, "u1", 30)
    assert called.get("spent")
