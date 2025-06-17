# Project Name: Thronestead©
# File Name: test_tax_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from services.tax_service import collect_alliance_tax


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self):
        self.vault = {"gold": 0}
        self.tax_rate = 5
        self.records = []
        self.vault_logs = []

    def execute(self, query, params=None):
        q = str(query)
        params = params or {}
        if "FROM alliance_tax_policies" in q:
            assert params.get("res") == "gold"
            assert "is_active = true" in q
            return DummyResult((self.tax_rate,))
        if q.startswith("UPDATE alliance_vault"):
            self.vault["gold"] += params.get("amt", 0)
            return DummyResult()
        if "INSERT INTO alliance_tax_collections" in q:
            self.records.append(
                {
                    "alliance_id": params.get("aid"),
                    "user_id": params.get("uid"),
                    "resource_type": params.get("res"),
                    "amount_collected": params.get("amt"),
                    "source": params.get("src"),
                    "notes": params.get("note"),
                }
            )
            return DummyResult()
        if "INSERT INTO alliance_vault_transaction_log" in q:
            self.vault_logs.append(params)
            return DummyResult()
        return DummyResult()

    def commit(self):
        pass


def test_collect_alliance_tax():
    db = DummyDB()
    net = collect_alliance_tax(db, 1, "u1", "gold", 1000, "income", "test")
    assert net == 950
    assert db.vault["gold"] == 50
    assert len(db.records) == 1
    assert db.records[0]["amount_collected"] == 50
    assert len(db.vault_logs) == 1
    assert db.vault_logs[0]["aid"] == 1
    assert db.vault_logs[0]["amt"] == 50
