from backend.routers.alliance_achievements import get_achievements, award, AwardPayload


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
        self.rows = []
        self.insert_params = []

    def execute(self, query, params=None):
        q = str(query)
        if "FROM users" in q or "FROM alliances" in q:
            return DummyResult((1,))
        if "FROM alliance_achievement_catalogue" in q and "LEFT JOIN" in q:
            return DummyResult(rows=self.rows)
        if q.strip().startswith("SELECT 1 FROM alliance_achievements"):
            return DummyResult(None)
        if q.strip().startswith("INSERT INTO alliance_achievements"):
            self.insert_params.append(params)
            return DummyResult()
        if "SELECT points_reward FROM alliance_achievement_catalogue" in q:
            return DummyResult((5,))
        return DummyResult()

    def commit(self):
        pass


def test_get_achievements_returns_rows():
    db = DummyDB()
    db.rows = [(
        "first",
        "First",
        "Desc",
        "military",
        5,
        "url",
        False,
        False,
        "2025-01-01",
    )]
    result = get_achievements(user_id="u1", db=db)
    assert result["achievements"][0]["achievement_code"] == "first"


def test_award_inserts_when_new():
    db = DummyDB()
    payload = AwardPayload(achievement_code="first")
    res = award(payload, user_id="u1", db=db)
    assert res["points_reward"] == 5
    assert db.insert_params
