from services.spies_service import reset_daily_attack_counts, get_spy_defense


class DummyResult:
    def __init__(self, rowcount=0):
        self.rowcount = rowcount


class DummyDB:
    def __init__(self, row=None):
        self.queries = []
        self.committed = False
        self.row = row

    def execute(self, query, params=None):
        self.queries.append(str(query).strip())
        if "spy_defense" in str(query):

            class R:
                def fetchone(_self):
                    return self.row

            return R()
        return DummyResult(rowcount=5)

    def commit(self):
        self.committed = True


def test_reset_daily_attack_counts():
    db = DummyDB()
    count = reset_daily_attack_counts(db)
    assert count == 5
    assert any("UPDATE kingdom_spies" in q for q in db.queries)
    assert db.committed


def test_get_spy_defense_returns_value():
    db = DummyDB(row=(3,))
    rating = get_spy_defense(db, 1)
    assert rating == 3
    assert any("spy_defense" in q for q in db.queries)


def test_get_spy_defense_default_zero():
    db = DummyDB(row=None)
    rating = get_spy_defense(db, 2)
    assert rating == 0
