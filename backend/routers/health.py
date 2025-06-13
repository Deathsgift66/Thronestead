from fastapi import APIRouter

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
def health_check():
    """Simple health check endpoint for uptime monitoring."""
    return {"status": "ok"}
