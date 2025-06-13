"""Minimal FastAPI entrypoint for local development."""

from fastapi import FastAPI

# Import routers from the backend package. ``login_routes`` contains the
# announcements endpoint, so alias it accordingly for clarity when including
# the router below.
from backend.routers import resources
from backend.routers import login_routes as announcements
from backend.routers import region


app = FastAPI()

app.include_router(resources.router)
app.include_router(announcements.router)
app.include_router(region.router)


if __name__ == "__main__":  # pragma: no cover - manual start
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
