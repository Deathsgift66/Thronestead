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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Router imports
from backend.routers import resources
from backend.routers import login_routes as announcements
from backend.routers import region
from backend.routers import progression_router

logger = logging.getLogger("KingmakersRise.Main")

app = FastAPI(
    title="Kingmaker's Rise API",
    version="6.14.2025.20.12",
    description="Backend services for Kingmaker's Rise — resource systems, announcements, region data, and progression.",
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
