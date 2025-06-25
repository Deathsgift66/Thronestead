# Project Name: Thronestead©
# File Name: main.py
# Version 6.14.2025.20.13
# Developer: Deathsgift66
"""Convenience entry point for running the Thronestead backend.

This file simply exposes ``app`` from :mod:`backend.main`, which contains the
full FastAPI application with all routers registered and the static frontend
mounted.
"""

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - allow running without dependency
    def load_dotenv(*_args, **_kwargs):
        """Fallback no-op if python-dotenv isn't installed."""
        print("\N{WARNING SIGN} python-dotenv not installed. Skipping .env loading.")
        return False

loaded = load_dotenv()
if not loaded:
    print("\N{WARNING SIGN} .env file not found. Continuing with system environment.")

from backend.main import app

if __name__ == "__main__":  # pragma: no cover - manual execution
    import os

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
