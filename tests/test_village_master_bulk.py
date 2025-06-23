from backend.routers.village_master import (
    bulk_harvest,
    bulk_queue_training,
    bulk_upgrade_all,
)


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
        return DummyResult()

    def commit(self):
        pass


def test_bulk_upgrade_executes_update():
    db = DummyDB()
    bulk_upgrade_all(user_id="u1", db=db)
    executed = " ".join(db.calls[1][0].split()).lower()
    assert "update village_buildings" in executed
    assert db.calls[1][1]["kid"] == 1


def test_bulk_queue_training_inserts():
    db = DummyDB()
    bulk_queue_training(user_id="u1", db=db)
    executed = " ".join(db.calls[1][0].split()).lower()
    assert "insert into training_queue" in executed


def test_bulk_harvest_updates_resources():
    db = DummyDB()
    bulk_harvest(user_id="u1", db=db)
    executed = " ".join(db.calls[1][0].split()).lower()
    assert "update village_resources" in executed
