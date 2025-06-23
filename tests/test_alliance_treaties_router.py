from backend.routers import alliance_treaties_router as router


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def mappings(self):
        return self

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.rows = []

    def execute(self, query, params=None):
        return DummyResult(rows=self.rows)


def test_get_treaty_types_returns_rows():
    db = DummyDB()
    db.rows = [{"treaty_type": "NAP", "display_name": "Non-Aggression Pact"}]
    result = router.get_treaty_types(db=db)
    assert result["types"][0]["treaty_type"] == "NAP"
