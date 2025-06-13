# Project Name: Kingmakers Rise©
# File Name: test_admin_war_actions.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from backend.routers.admin_dashboard import force_end_war, rollback_combat_tick, WarAction

class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []
    def fetchall(self):
        return self._rows
    def fetchone(self):
        return None

class DummyDB:
    def __init__(self):
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append((str(query), params))
        return DummyResult()
    def commit(self):
        pass


def test_force_end_war_updates_and_logs():
    db = DummyDB()
    force_end_war(WarAction(war_id=1), admin_user_id="a1", db=db)
    executed = " ".join(db.queries[0][0].split()).lower()
    assert "update wars_tactical" in executed
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)


def test_rollback_combat_tick_updates_and_logs():
    db = DummyDB()
    rollback_combat_tick(WarAction(war_id=2), admin_user_id="a1", db=db)
    executed = " ".join(db.queries[0][0].split()).lower()
    assert "update wars_tactical" in executed
    assert any("delete from combat_logs" in q[0].lower() for q in db.queries)
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)
