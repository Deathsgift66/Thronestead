# Project Name: Kingmakers Rise©
# File Name: main.py
# Version 6.14.2025.20.12
# Developer: Deathsgift66

"""
Entrypoint for the FastAPI application — used for local dev and deployment.

Routers:
- /api/resources
- /api/announcements
- /api/regions
- /api/progression
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.auth_middleware import UserStateMiddleware
import logging
import os

# Ensure environment variables from `.ENV` are loaded via the backend package
import backend as _backend  # noqa: F401

# Router imports
from backend.routers import resources
from backend.routers import login_routes as announcements
from backend.routers import region
from backend.routers import progression_router

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("KingmakersRise.Main")

app = FastAPI(
    title="Kingmaker's Rise API",
    version="6.14.2025.20.12",
    description="Backend services for Kingmaker's Rise — resource systems, announcements, region data, and progression.",
)


# Generic catch-all error handler for unexpected exceptions
@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    logger.exception("Unhandled application error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


# Configure CORS
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    origins = []  # Default to no CORS if environment variable is missing
    logger.warning("ALLOWED_ORIGINS not set; CORS disabled for external domains.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(UserStateMiddleware)

# Register all route modules
# Each router already defines its API prefix and tags.
app.include_router(resources.router)
app.include_router(announcements.router)
app.include_router(region.router)
app.include_router(progression_router.router)

# Manual launch for `python main.py` use
if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
