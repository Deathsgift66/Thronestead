# Project Name: Thronestead©
# File Name: test_kingdom_troops_router.py
# Version 6.14.2025
# Developer: Codex
from fastapi import HTTPException

from backend.routers.kingdom_troops import unlocked_troops, upgrade_troops, UpgradePayload


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
        self.calls = []
        self.castle_row = (1,)
        self.tech_rows = []
        self.rows = []
        self.upgrade_path = {
            "required_level": 1,
            "cost": {"xp": 5},
            "wood": 2,
        }
        self.troop_row = (10, 6)
        self.resource_row = (10,)

    def execute(self, query, params=None):
        q = str(query)
        self.calls.append((q, params))
        if "kingdom_castle_progression" in q:
            return DummyResult(row=self.castle_row)
        if "kingdom_research_tracking" in q:
            return DummyResult(rows=self.tech_rows)
        if "FROM training_catalog" in q:
            return DummyResult(rows=self.rows)
        if "FROM unit_upgrade_paths" in q:
            up = self.upgrade_path
            if up:
                return DummyResult(
                    row=(up["required_level"], up["cost"], up["wood"])
                )
            return DummyResult()
        if "FROM kingdom_troops" in q:
            return DummyResult(row=self.troop_row)
        if "FROM kingdom_resources" in q:
            return DummyResult(row=self.resource_row)
        return DummyResult()

    def commit(self):
        pass


def test_unlocked_troops_filters_prereqs():
    db = DummyDB()
    db.rows = [
        (
            "Spearman",
            None,
            1,
            "Spearman",
            1,
            "Infantry",
            5,
            2,
            10,
            3,
            1,
        ),
        (
            "Knight",
            "horsemanship",
            2,
            "Knight",
            2,
            "Cavalry",
            7,
            4,
            15,
            5,
            1,
        ),
    ]
    result = unlocked_troops(user_id="u1", db=db)
    assert result["unlockedUnits"] == ["Spearman"]
    assert "Knight" not in result["unitStats"]


def test_unlocked_troops_with_tech_and_level():
    db = DummyDB()
    db.castle_row = (3,)
    db.tech_rows = [("horsemanship",)]
    db.rows = [
        (
            "Knight",
            "horsemanship",
            2,
            "Knight",
            2,
            "Cavalry",
            7,
            4,
            15,
            5,
            1,
        )
    ]
    result = unlocked_troops(user_id="u1", db=db)
    assert result["unlockedUnits"] == ["Knight"]
    assert result["unitStats"]["Knight"]["tier"] == 2


def test_upgrade_troops_success():
    db = DummyDB()
    payload = UpgradePayload(from_unit="Spearman", to_unit="Pikeman", quantity=5)
    res = upgrade_troops(payload, user_id="u1", db=db)
    assert res["status"] == "upgraded"


def test_upgrade_troops_not_enough_xp():
    db = DummyDB()
    db.troop_row = (10, 2)
    payload = UpgradePayload(from_unit="Spearman", to_unit="Pikeman", quantity=5)
    try:
        upgrade_troops(payload, user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 400
    else:
        assert False, "Expected HTTPException"
