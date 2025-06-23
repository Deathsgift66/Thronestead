# Project Name: Thronestead©
# File Name: main.py
# Version 6.14.2025.20.13
# Developer: Deathsgift66
"""Convenience entry point for running the Thronestead backend.

This file simply exposes ``app`` from :mod:`backend.main`, which contains the
full FastAPI application with all routers registered and the static frontend
mounted.
"""

from backend.main import app

if __name__ == "__main__":  # pragma: no cover - manual execution
    import uvicorn
    import os

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
