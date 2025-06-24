from backend.routers import faith


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self):
        self.queries = []
        self.committed = False

    def execute(self, query, params=None):
        q = str(query).lower()
        self.queries.append((q, params))
        if "from kingdoms" in q:
            return DummyResult((1,))
        if "from kingdom_religion" in q:
            return DummyResult((2, 50, {}))
        return DummyResult()

    def commit(self):
        self.committed = True


def test_get_faith():
    db = DummyDB()
    result = faith.get_faith(user_id="u1", db=db)
    assert result["faith_level"] == 2
    assert result["faith_points"] == 50
