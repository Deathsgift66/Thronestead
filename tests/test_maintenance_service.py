from services import maintenance_service
from services import resource_service


class DummyResult:
    def __init__(self, rowcount=0, rows=None):
        self.rowcount = rowcount
        self._rows = rows or []

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.queries = []
        self.commits = 0
        self.rows = [(1,), (2,)]

    def execute(self, query, params=None):
        self.queries.append(str(query).strip())
        if "FROM kingdoms" in str(query):
            return DummyResult(rows=self.rows)
        return DummyResult(rowcount=5)

    def commit(self):
        self.commits += 1


def test_verify_kingdom_resources(monkeypatch):
    db = DummyDB()
    called = []
    monkeypatch.setattr(resource_service, "ensure_kingdom_resource_row", lambda d, k: called.append(k))

    count = maintenance_service.verify_kingdom_resources(db)

    assert count == 2
    assert called == [1, 2]
    assert db.commits == 1
    assert any("kingdoms" in q for q in db.queries)


def test_cleanup_zombie_training_queue():
    db = DummyDB()

    count = maintenance_service.cleanup_zombie_training_queue(db)

    assert count == 5
    assert db.commits == 1
    assert any("DELETE FROM training_queue" in q for q in db.queries)


def test_cleanup_zombie_spy_missions():
    db = DummyDB()

    count = maintenance_service.cleanup_zombie_spy_missions(db)

    assert count == 5
    assert db.commits == 1
    assert any("UPDATE spy_missions" in q for q in db.queries)
