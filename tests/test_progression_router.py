# Project Name: Thronestead©
# File Name: test_progression_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from backend.routers import progression_router as pr


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None):
        q = str(query)
        self.calls.append((q, params))
        if "FROM kingdoms" in q:
            return DummyResult((1,))
        if "kingdom_castle_progression" in q:
            return DummyResult((3,))
        if "kingdom_nobles" in q:
            return DummyResult((2,))
        if "kingdom_knights" in q:
            return DummyResult((5,))
        if "kingdom_villages" in q:
            return DummyResult((3,))
        if "kingdom_troop_slots" in q:
            if "used_slots" in q:
                return DummyResult((6,))
        return DummyResult(None)

    def commit(self):
        pass


def test_progression_summary_returns_data():
    db = DummyDB()
    pr.calculate_troop_slots = lambda db, kid: 10
    result = pr.progression_summary(user_id="u1", db=db)
    assert result["castle_level"] == 3
    assert result["nobles_total"] == 2
    assert result["knights_total"] == 5
    assert result["troop_slots"]["used"] == 6
    assert result["troop_slots"]["available"] == 4



def test_rename_knight_updates_name(monkeypatch):
    class RenameDB(DummyDB):
        def __init__(self):
            super().__init__()
            self.rows = {"select": DummyResult((1,))}

        def execute(self, query, params=None):
            q = str(query)
            self.calls.append((q, params))
            if "SELECT knight_id" in q:
                return self.rows["select"]
            return DummyResult()

    db = RenameDB()

    monkeypatch.setattr(pr, "get_kingdom_id", lambda d, u: 1)
    payload = pr.KnightRenamePayload(current_name="Old", new_name="New")
    pr.rename_knight(payload, user_id="u1", db=db)
    executed = " ".join(db.calls[-1][0].split()).lower()
    assert "update kingdom_knights" in executed


def test_upgrade_castle_explicit_calls_base(monkeypatch):
    dummy_db = DummyDB()

    def fake_upgrade_castle(user_id: str, db: DummyDB):
        assert user_id == "u1"
        assert db is dummy_db
        return {"message": "ok"}

    monkeypatch.setattr(pr, "upgrade_castle", fake_upgrade_castle)
    result = pr.upgrade_castle_explicit(user_id="u1", db=dummy_db)
    assert result["message"] == "ok"

