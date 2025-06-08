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

    def execute(self, query, params=None):
        q = str(query)
        params = params or {}
        if "FROM alliance_tax_policies" in q:
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
