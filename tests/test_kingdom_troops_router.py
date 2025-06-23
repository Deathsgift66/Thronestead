# Project Name: Thronestead©
# File Name: test_kingdom_troops_router.py
# Version 6.14.2025
# Developer: Codex
from backend.routers.kingdom_troops import unlocked_troops


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

    def execute(self, query, params=None):
        q = str(query)
        self.calls.append((q, params))
        if "kingdom_castle_progression" in q:
            return DummyResult(row=self.castle_row)
        if "kingdom_research_tracking" in q:
            return DummyResult(rows=self.tech_rows)
        if "FROM training_catalog" in q:
            return DummyResult(rows=self.rows)
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
