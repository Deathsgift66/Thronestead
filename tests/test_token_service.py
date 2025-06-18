from services import token_service

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
        if str(query).lower().startswith('select tokens'):
            return DummyResult(self.row)
        return DummyResult()
    def commit(self):
        self.committed = True


def test_get_balance_returns_zero_when_missing():
    db = DummyDB()
    assert token_service.get_balance(db, 'u') == 0


def test_consume_tokens_blocks_if_insufficient():
    db = DummyDB()
    db.row = (1,)
    assert not token_service.consume_tokens(db, 'u', 5)


def test_add_tokens_executes_insert():
    db = DummyDB()
    token_service.add_tokens(db, 'u', 2)
    assert any('insert into user_tokens' in q.lower() for q in db.queries)
    assert db.committed

