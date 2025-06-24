from services.alliance_achievement_service import award_achievement, list_achievements


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
        self.points = None
        self.list_rows = []

    def execute(self, query, params=None):
        q = str(query).strip()
        params = params or {}
        if q.startswith("SELECT 1 FROM alliance_achievements"):
            return DummyResult(self.check_rows.pop(0) if self.check_rows else None)
        if q.startswith("INSERT INTO alliance_achievements"):
            self.inserted.append(params)
            return DummyResult()
        if "SELECT points_reward FROM alliance_achievement_catalogue" in q:
            return DummyResult((self.points,))
        if "FROM alliance_achievement_catalogue" in q and "LEFT JOIN" in q:
            return DummyResult(rows=self.list_rows)
        return DummyResult()

    def commit(self):
        pass


def test_award_new_achievement():
    db = DummyDB()
    db.check_rows = [None]
    db.points = 10
    points = award_achievement(db, 2, "first")
    assert points == 10
    assert db.inserted[0]["aid"] == 2


def test_award_existing_returns_none():
    db = DummyDB()
    db.check_rows = [(1,)]
    points = award_achievement(db, 2, "first")
    assert points is None
    assert not db.inserted


def test_list_achievements_filters_hidden():
    db = DummyDB()
    db.list_rows = [
        ("first", "First", "Desc", "general", 5, "url", False, False, None),
        ("secret", "Secret", "Hidden", "general", 5, "url", True, False, None),
        ("done", "Done", "", "military", 3, "u", False, False, "2025-01-01"),
    ]
    res = list_achievements(db, 1)
    codes = [r["achievement_code"] for r in res]
    assert "first" in codes
    assert "done" in codes
    assert "secret" not in codes
