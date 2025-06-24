from services.combat_log_service import apply_war_outcome_morale

class DummyResult:
    def __init__(self, row=None, rowcount=0):
        self._row = row
        self.rowcount = rowcount
    def fetchone(self):
        return self._row

class DummyDB:
    def __init__(self):
        self.queries = []
        self.commits = 0
    def execute(self, query, params=None):
        q = str(query).strip()
        self.queries.append(q)
        if "FROM wars" in q:
            return DummyResult(row=(1, 2, 'attacker_win'))
        return DummyResult(rowcount=1)
    def commit(self):
        self.commits += 1


def test_apply_war_outcome_morale_updates():
    db = DummyDB()
    count = apply_war_outcome_morale(db, 5)
    assert count == 2
    joined = " ".join(db.queries)
    assert "kingdom_troop_slots" in joined

