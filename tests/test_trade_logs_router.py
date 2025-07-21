# Project Name: Thronestead©
# File Name: test_trade_logs_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
import os
import sys
from datetime import datetime
import pytest
from fastapi import HTTPException

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.routers import trade_logs


class DummyQuery:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, *_args):
        return self

    def all(self):
        return self.rows


class DummySession:
    def __init__(self, rows):
        self._query = DummyQuery(rows)

    def query(self, _model):
        return self._query


def test_get_trade_logs_returns_rows():
    row = type(
        "Row",
        (),
        {
            "trade_id": 1,
            "timestamp": datetime(2025, 1, 1),
            "resource": "Wood",
            "quantity": 5,
            "unit_price": 2.0,
            "buyer_id": "b1",
            "seller_id": "s1",
            "buyer_alliance_id": 1,
            "seller_alliance_id": 1,
            "buyer_name": "B",
            "seller_name": "S",
            "trade_type": "market",
            "trade_status": "completed",
            "initiated_by_system": False,
        },
    )
    db = DummySession([row])
    result = trade_logs.get_trade_logs(db=db, user_id="u1")
    assert result["logs"][0]["resource"] == "Wood"


def test_invalid_start_date():
    db = DummySession([])
    with pytest.raises(HTTPException) as exc:
        trade_logs.get_trade_logs(start_date="bad", db=db, user_id="u1")
    assert exc.value.status_code == 400


def test_invalid_end_date():
    db = DummySession([])
    with pytest.raises(HTTPException) as exc:
        trade_logs.get_trade_logs(end_date="nope", db=db, user_id="u1")
    assert exc.value.status_code == 400
