import services.combat_tick_engine as combat_tick_engine


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.queries = []
        self.commit_count = 0
        self.rollback_count = 0
        self.rows = []
        self.duplicate = False

    def execute(self, query, params=None):
        q = str(query).strip()
        self.queries.append(q)
        if "SELECT war_id, battle_tick" in q:
            return DummyResult(self.rows)
        if "INSERT INTO tick_execution_log" in q and self.duplicate:
            raise Exception("duplicate")
        return DummyResult()

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1


def test_process_combat_tick_inserts_and_updates():
    db = DummyDB()
    ok = combat_tick_engine.process_combat_tick(db, 1, 5, {"o": True})
    assert ok
    joined = " ".join(db.queries).lower()
    assert "combat_tick_queue_backup" in joined
    assert "tick_execution_log" in joined
    assert "update wars_tactical" in joined
    assert db.commit_count == 1


def test_process_combat_tick_duplicate_returns_false():
    db = DummyDB()
    db.duplicate = True
    ok = combat_tick_engine.process_combat_tick(db, 1, 5, {})
    assert not ok
    assert db.rollback_count == 1


def test_watchdog_restart_calls_process(monkeypatch):
    db = DummyDB()
    db.rows = [(1, 2), (2, 3)]
    called = []

    def fake_process(d, wid, tick, payload):
        called.append((wid, tick))
        return True

    monkeypatch.setattr(combat_tick_engine, "process_combat_tick", fake_process)
    count = combat_tick_engine.watchdog_restart(db, 300)
    assert count == 2
    assert called == [(1, 3), (2, 4)]
