from services.spies_service import reset_daily_attack_counts


class DummyResult:
    def __init__(self, rowcount=0):
        self.rowcount = rowcount


class DummyDB:
    def __init__(self):
        self.queries = []
        self.committed = False

    def execute(self, query, params=None):
        self.queries.append(str(query).strip())
        return DummyResult(rowcount=5)

    def commit(self):
        self.committed = True


def test_reset_daily_attack_counts():
    db = DummyDB()
    count = reset_daily_attack_counts(db)
    assert count == 5
    assert any("UPDATE kingdom_spies" in q for q in db.queries)
    assert db.committed

