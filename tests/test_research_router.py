from backend.routers.kingdom import research_list

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
        self.catalog_rows = [
            ("t1", [], 1, None),
            ("t2", ["t1"], 1, None),
        ]
        self.tracking_rows = [("t1", "completed", "2025-01-01")]
        self.castle_row = (1,)
        self.region_row = ("north",)

    def execute(self, query, params=None):
        q = str(query).lower()
        self.calls.append(q)
        if "select kingdom_id from kingdoms where user_id" in q:
            return DummyResult(row=(1,))
        if "update kingdom_research_tracking" in q:
            return DummyResult()
        if "from kingdom_research_tracking" in q:
            return DummyResult(rows=self.tracking_rows)
        if "from kingdom_castle_progression" in q:
            return DummyResult(row=self.castle_row)
        if "from kingdoms where kingdom_id" in q:
            return DummyResult(row=self.region_row)
        if "from tech_catalogue" in q:
            return DummyResult(rows=self.catalog_rows)
        return DummyResult()

    def commit(self):
        pass


def test_research_list_returns_available():
    db = DummyDB()
    result = research_list(user_id="u1", db=db)
    assert result["completed"][0]["tech_code"] == "t1"
    assert "t2" in result["available"]
