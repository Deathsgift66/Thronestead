# Project Name: Thronestead©
# File Name: test_trade_log_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from services.trade_log_service import record_trade, update_trade_status


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self):
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append((str(query), params))
        if str(query).strip().startswith("INSERT INTO trade_logs"):
            return DummyResult((1,))
        return DummyResult()

    def commit(self):
        pass


def test_record_trade_inserts():
    db = DummyDB()
    tid = record_trade(
        db,
        resource="gold",
        quantity=10,
        unit_price=1.5,
        buyer_id="b1",
        seller_id="s1",
        buyer_alliance_id=1,
        seller_alliance_id=2,
        buyer_name="B",
        seller_name="S",
        trade_type="market_sale",
    )
    assert tid == 1
    assert len(db.executed) == 1
    assert "INSERT INTO trade_logs" in db.executed[0][0]


def test_update_trade_status():
    db = DummyDB()
    update_trade_status(db, 5, "refunded")
    assert len(db.executed) == 1
    assert "UPDATE trade_logs" in db.executed[0][0]
    assert db.executed[0][1]["st"] == "refunded"
