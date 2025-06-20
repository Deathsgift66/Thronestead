# Project Name: Thronestead©
# File Name: main.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""FastAPI application for the Thronestead backend.

This module loads all API routers, ensures the database schema exists, and
serves the static frontend.  It can be imported as ``backend.main`` or run
directly for development purposes.
"""

# Allow running this file directly via ``python backend/main.py`` by adjusting
# ``sys.path`` so that relative imports resolve correctly.
if __name__ == "__main__" and __package__ is None:  # pragma: no cover - dev only
    from pathlib import Path
    import sys

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "backend"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth_middleware import UserStateMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import os

from .database import engine
from .models import Base
from .data import load_game_settings
from . import routers as router_pkg

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("Thronestead.BackendMain")

# -----------------------
# ⚙️ FastAPI Initialization
# -----------------------
app = FastAPI(
    title="Thronestead API",
    version="6.13.2025.19.49",
    description="Backend for the Thronestead strategy MMO.",
)

# -----------------------
# 🔐 Middleware (CORS, security headers, etc.)
# -----------------------
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    if allowed_origins_env.strip() == "*":
        origins = ["*"]
        allow_credentials = False
        logger.warning("CORS allowing any origin without credentials")
    else:
        origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
        allow_credentials = True
else:
    origins = [
        "https://thronestead.com",
        "https://www.thronestead.com",
        "http://localhost:5173",
    ]
    allow_credentials = True
    logger.warning(
        "ALLOWED_ORIGINS not set; defaulting to production and localhost"
    )

cors_options = {
    "allow_origins": origins,
    "allow_credentials": allow_credentials,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
app.add_middleware(CORSMiddleware, **cors_options)
app.add_middleware(UserStateMiddleware)

# -----------------------
# 🗃️ Ensure Database Tables Exist
# -----------------------
if engine:
    Base.metadata.create_all(bind=engine)

# Load game-wide settings into memory (affects all systems)
load_game_settings()

# -----------------------
# 📦 Route Imports and Inclusion
# -----------------------

for name in router_pkg.__all__:
    module = getattr(router_pkg, name)
    router_obj = getattr(module, "router", None)
    if router_obj:
        app.include_router(router_obj)
    alt_obj = getattr(module, "alt_router", None)
    if alt_obj:
        app.include_router(alt_obj)

# -----------------------
# 🖼️ Serve Static Frontend Files
# -----------------------
# ``FRONTEND_DIR`` can override the default directory for serving the static site
BASE_DIR = Path(os.getenv("FRONTEND_DIR", Path(__file__).resolve().parent.parent))
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")

# -----------------------
# ✅ Health Check (used by Render or CI/CD)
# -----------------------
@app.get("/health-check")
def health_check():
    """Simple endpoint used for uptime checks and load balancers."""
    return {"status": "online", "service": "Thronestead API"}


if __name__ == "__main__":  # pragma: no cover - manual execution
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
