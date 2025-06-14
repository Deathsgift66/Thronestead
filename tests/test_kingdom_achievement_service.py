# Project Name: Kingmakers Rise©
# File Name: test_kingdom_achievement_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from services.kingdom_achievement_service import award_achievement, list_achievements


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
        self.inserted = []
        self.check_rows = []
        self.reward = None
        self.list_rows = []

    def execute(self, query, params=None):
        q = str(query).strip()
        params = params or {}
        if q.startswith("SELECT 1 FROM kingdom_achievements"):
            return DummyResult(self.check_rows.pop(0) if self.check_rows else None)
        if q.startswith("INSERT INTO kingdom_achievements"):
            self.inserted.append(params)
            return DummyResult()
        if "SELECT reward FROM kingdom_achievement_catalogue" in q:
            return DummyResult((self.reward,))
        if "FROM kingdom_achievement_catalogue" in q and "LEFT JOIN" in q:
            return DummyResult(rows=self.list_rows)
        return DummyResult()

    def commit(self):
        pass


def test_award_new_achievement():
    db = DummyDB()
    db.check_rows = [None]
    db.reward = {"gold": 100}
    reward = award_achievement(db, 1, "first_gold")
    assert reward == {"gold": 100}
    assert db.inserted[0]["kid"] == 1


def test_award_existing_returns_none():
    db = DummyDB()
    db.check_rows = [(1,)]
    reward = award_achievement(db, 1, "first_gold")
    assert reward is None
    assert db.inserted == []


def test_list_achievements_filters_hidden():
    db = DummyDB()
    db.list_rows = [
        ("first_gold", "First Gold", "Earn 1000", "economic", {"gold": 100}, 5, False, None),
        ("secret", "Secret", "Hidden details", "exploration", {}, 0, True, None),
        ("battle", "Battle", "Win", "military", {}, 10, False, "2025-01-01"),
    ]
    results = list_achievements(db, 1)
    codes = [r["achievement_code"] for r in results]
    assert "first_gold" in codes
    assert "battle" in codes
    assert "secret" not in codes
