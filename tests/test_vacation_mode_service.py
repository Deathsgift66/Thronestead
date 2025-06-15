# Project Name: Kingmakers Rise©
# File Name: test_vacation_mode_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from datetime import datetime, timedelta

from fastapi import HTTPException

from services.vacation_mode_service import (
    enter_vacation_mode,
    exit_vacation_mode,
    can_exit_vacation,
    check_vacation_mode,
)


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self):
        self.queries = []
        self.params = []
        self.row = None
        self.committed = False

    def execute(self, query, params=None):
        self.queries.append(str(query))
        self.params.append(params)
        return DummyResult(self.row)

    def commit(self):
        self.committed = True


def test_enter_and_exit():
    db = DummyDB()
    enter_vacation_mode(db, 1)
    assert any("UPDATE kingdoms" in q for q in db.queries)
    assert db.committed
    db.committed = False
    exit_vacation_mode(db, 1)
    assert any("is_on_vacation = FALSE" in q for q in db.queries[-1:])
    assert db.committed


def test_can_exit_vacation():
    db = DummyDB()
    db.row = (datetime.utcnow() - timedelta(days=1),)
    assert can_exit_vacation(db, 1)
    db.row = (datetime.utcnow() + timedelta(days=1),)
    assert not can_exit_vacation(db, 1)


def test_check_vacation_mode_raises():
    db = DummyDB()
    db.row = (True,)
    raised = False
    try:
        check_vacation_mode(db, 1)
    except HTTPException:
        raised = True
    assert raised

