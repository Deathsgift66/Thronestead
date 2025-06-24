from services import faith_service


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self, points=0, level=1):
        self.points = points
        self.level = level
        self.saved = None
        self.queries = []
        self.committed = False
        self.bless = {}

    def execute(self, query, params=None):
        q = str(query).lower()
        self.queries.append(q)
        if "select faith_points" in q:
            return DummyResult((self.points, self.level))
        if "select blessings" in q:
            return DummyResult((self.bless,))
        if q.strip().startswith("update kingdom_religion"):
            self.saved = params
            self.points = params.get("pts", self.points)
            self.level = params.get("lvl", self.level)
            self.bless = params.get("b", self.bless)
            return DummyResult()
        if q.strip().startswith("insert into kingdom_religion"):
            return DummyResult()
        return DummyResult()

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_gain_faith_levels_up():
    db = DummyDB(points=0, level=1)
    faith_service.gain_faith(db, 1, faith_service.FAITH_PER_LEVEL + 10)
    assert db.committed
    assert db.saved["lvl"] == 2
    assert db.saved["pts"] == 10
