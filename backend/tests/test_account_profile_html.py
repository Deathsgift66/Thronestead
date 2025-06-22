"""
Project: Thronestead ©
File: test_account_profile_html.py
Role: Unit tests for test account profile html.
Version: 2025-06-21
"""

import pytest
from httpx import AsyncClient
from backend.main import app

@pytest.mark.asyncio
async def test_account_profile_template():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/account/profile")
        assert response.status_code == 200
