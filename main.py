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

# Router imports
from backend.routers import resources
from backend.routers import login_routes as announcements
from backend.routers import region
from backend.routers import progression_router

app = FastAPI(
    title="Kingmaker's Rise API",
    version="6.14.2025.20.12",
    description="Backend services for Kingmaker's Rise — resource systems, announcements, region data, and progression."
)

# Optional: Allow all for development CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend domain(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route modules
app.include_router(resources.router, prefix="/api/resources", tags=["resources"])
app.include_router(announcements.router, prefix="/api/announcements", tags=["announcements"])
app.include_router(region.router, prefix="/api/regions", tags=["regions"])
app.include_router(progression_router.router, prefix="/api/progression", tags=["progression"])

# Manual launch for `python main.py` use
if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
