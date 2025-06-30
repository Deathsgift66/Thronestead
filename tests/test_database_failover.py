import backend.database as database

class DummyEngine:
    pass


def test_read_replica_failover(monkeypatch):
    primary = 'postgres://primary'
    replica = 'postgres://replica'
    monkeypatch.setenv('DATABASE_URL', primary)
    monkeypatch.setenv('READ_REPLICA_URL', replica)

    calls = []

    def create_engine(url, **kwargs):
        calls.append(url)
        if url == primary:
            raise database.OperationalError('x', 'y', 'z')
        return DummyEngine()

    monkeypatch.setattr(database, 'create_engine', create_engine)
    monkeypatch.setattr(database, 'sessionmaker', lambda bind, **k: lambda: None)

    database.init_engine()

    assert calls == [primary, replica]
    assert isinstance(database.engine, DummyEngine)
