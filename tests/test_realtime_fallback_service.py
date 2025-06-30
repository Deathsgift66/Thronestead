from services.realtime_fallback_service import (
    fallback_on_idle_training,
    mark_stale_engaged_units_defeated,
)


class DummyResult:
    def __init__(self, rowcount=0):
        self.rowcount = rowcount


class DummyDB:
    def __init__(self):
        self.queries = []
        self.committed = False

    def execute(self, query, params=None):
        self.queries.append(str(query).lower())
        return DummyResult(rowcount=5)

    def commit(self):
        self.committed = True


def test_fallback_on_idle_training():
    db = DummyDB()
    count = fallback_on_idle_training(db, gap_seconds=3600)
    assert count == 5
    assert any("update training_queue" in q for q in db.queries)
    assert db.committed


def test_mark_stale_engaged_units_defeated():
    db = DummyDB()
    count = mark_stale_engaged_units_defeated(db, stale_seconds=900)
    assert count == 5
    assert any("update unit_movements" in q for q in db.queries)
    assert db.committed
