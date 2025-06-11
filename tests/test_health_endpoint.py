import asyncio
from backend.main import healthcheck


def test_healthcheck_returns_ok():
    result = asyncio.run(healthcheck())
    assert result == {"status": "ok"}
