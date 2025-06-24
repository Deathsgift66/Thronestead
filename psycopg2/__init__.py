import types, sys

class RealDictCursor:
    pass

extras = types.ModuleType("psycopg2.extras")
extras.RealDictCursor = RealDictCursor
sys.modules[__name__ + '.extras'] = extras

class _DummyCursor:
    description = None
    def execute(self, *a, **k):
        pass
    def fetchall(self):
        return []
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass

class _DummyConn:
    def cursor(self):
        return _DummyCursor()
    def commit(self):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass

def connect(*args, **kwargs):
    return _DummyConn()
