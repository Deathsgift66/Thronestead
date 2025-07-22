from backend.routers import admin as admin_router


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.queries = []
        self.rows = []

    def execute(self, query, params=None):
        q = str(query)
        self.queries.append((q, params))
        lower = q.strip().lower()
        if lower.startswith("select is_admin"):
            return DummyResult([(True,)])
        if "from backup_queues" in lower:
            return DummyResult(self.rows)
        return DummyResult()

    def commit(self):
        pass


def test_reprocess_tick_logs():
    db = DummyDB()
    admin_router.reprocess_tick(admin_router.WarTick(war_id=1), admin_user_id="a", db=db)
    assert any("reprocess_war_tick" in q[0].lower() for q in db.queries)
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)


def test_recalculate_resources_logs():
    db = DummyDB()
    admin_router.recalculate_resources(admin_router.KingdomPayload(kingdom_id=2), admin_user_id="a", db=db)
    assert any("recalc_resources" in q[0].lower() for q in db.queries)
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)


def test_rollback_quest_logs():
    db = DummyDB()
    admin_router.rollback_quest(admin_router.QuestRollback(alliance_id=3, quest_code="Q"), admin_user_id="a", db=db)
    assert any("rollback_alliance_quest" in q[0].lower() for q in db.queries)
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)


def test_list_backup_queues():
    db = DummyDB()
    db.rows = [("nightly",), ("hourly",)]
    res = admin_router.list_backup_queues(admin_user_id="a", db=db)
    assert res["queues"] == ["nightly", "hourly"]
