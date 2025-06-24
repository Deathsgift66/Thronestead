from services.strategic_tick_service import activate_pending_wars
from services.war_battle_service import conclude_battle
import services.combat_log_service as combat_logs


class DummyResult:
    def __init__(self, row=None, rows=None, rowcount=0):
        self._row = row
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.queries = []
        self.rows = []
        self.row = None
        self.commits = 0

    def execute(self, query, params=None):
        q = str(query).strip()
        self.queries.append(q)
        if q.startswith("UPDATE wars") and "RETURNING" in q:
            return DummyResult(rows=self.rows)
        if "attacker_kingdom_id" in q and "defender_kingdom_id" in q:
            return DummyResult(row=self.row)
        return DummyResult(rowcount=1)

    def commit(self):
        self.commits += 1


def test_activate_pending_wars_sets_combat_flags():
    db = DummyDB()
    db.rows = [(1, 2, 3)]
    count = activate_pending_wars(db)
    assert count == 1
    joined = " ".join(db.queries)
    assert "kingdom_troop_slots" in joined
    assert db.commits == 1


def test_conclude_battle_resets_combat_flags(monkeypatch):
    db = DummyDB()
    db.row = (2, 3)
    monkeypatch.setattr(combat_logs, "apply_war_outcome_morale", lambda d, w: None)
    conclude_battle(db, 5)
    joined = " ".join(db.queries)
    assert "kingdom_troop_slots" in joined
    assert db.commits == 1
