# Project Name: Kingmakers Rise©
# File Name: test_public_config_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import os
import asyncio
from backend.routers import public_config


def test_public_config_returns_env_values():
    os.environ["SUPABASE_URL"] = "url"
    os.environ["SUPABASE_ANON_KEY"] = "anon"
    result = asyncio.run(public_config.public_config())
    assert result == {"SUPABASE_URL": "url", "SUPABASE_ANON_KEY": "anon"}
