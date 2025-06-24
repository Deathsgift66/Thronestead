import pytest

from services.alliance_vault_service import deposit_to_vault, withdraw_from_vault


class DummyDB:
    def __init__(self):
        self.queries = []
        self.committed = False

    def execute(self, query, params=None):
        self.queries.append((str(query), params or {}))
        return None

    def commit(self):
        self.committed = True


def test_invalid_resource_rejected():
    db = DummyDB()
    with pytest.raises(ValueError):
        deposit_to_vault(db, 1, "u1", "fake", 10)
    with pytest.raises(ValueError):
        withdraw_from_vault(db, 1, "u1", "fake", 5)


def test_valid_deposit_and_withdraw():
    db = DummyDB()
    deposit_to_vault(db, 1, "u1", "gold", 10)
    withdraw_from_vault(db, 1, "u1", "gold", 5)
    assert db.committed
    assert len(db.queries) >= 4
