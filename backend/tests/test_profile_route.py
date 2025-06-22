"""
Project: Thronestead ©
File: test_profile_route.py
Role: Unit tests for test profile route.
Version: 2025-06-21
"""

import pytest
from httpx import AsyncClient
from backend.main import app

@pytest.mark.asyncio
async def test_profile_route():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/profile")
        assert response.status_code == 200
