# Project Name: Thronestead©
# File Name: test_account_delete_router.py
# Version 6.15.2025
# Developer: OpenAI Codex
from fastapi import HTTPException

from backend.routers import account_delete


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self, exists=True):
        self.exists = exists
        self.queries = []
        self.committed = False

    def execute(self, query, params=None):
        txt = str(query).lower().strip()
        self.queries.append(txt)
        if "from users" in txt:
            return DummyResult((1,) if self.exists else None)
        return DummyResult()

    def commit(self):
        self.committed = True


def test_delete_account_updates_row():
    db = DummyDB()
    account_delete.log_action = lambda *a, **k: None
    result = account_delete.delete_account(user_id="u1", db=db)
    assert result["status"] == "deleted"
    joined = " ".join(db.queries[-1].split())
    assert "update users" in joined
    assert "is_deleted" in joined
    assert db.committed


def test_delete_account_user_missing():
    db = DummyDB(exists=False)
    account_delete.log_action = lambda *a, **k: None
    try:
        account_delete.delete_account(user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        assert False
