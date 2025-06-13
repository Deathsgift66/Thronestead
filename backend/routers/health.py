# Project Name: Kingmakers Rise©
# File Name: health.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
def health_check():
    """Simple health check endpoint for uptime monitoring."""
    return {"status": "ok"}
