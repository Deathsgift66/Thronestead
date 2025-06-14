# 🧪 Test Harness Bootstrap

## Install Dev Requirements
```bash
pip install -r requirements-dev.txt
```

## Mocking Supabase/DB
Use `pytest-asyncio`, `unittest.mock`, and factory fixtures:

```python
@pytest.fixture
def mock_db():
    with patch("backend.database.get_db") as db:
        yield db
```

## Run Tests
```bash
pytest tests/ -v --maxfail=5
```

## Coverage
- Routers: `/api/projects`, `/api/quests`, `/api/battle`
- Services: `progression_service`, `strategic_tick_service`
- Fixtures: `kingdom_factory`, `quest_factory`, `modifier_factory`