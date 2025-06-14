# Project Name: Kingmakers Rise©
# File Name: main.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Main application entry point for the FastAPI server powering Kingmakers Rise©.
Loads routers, initializes the DB schema, and serves static frontend content.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import os

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("KingmakersRise.BackendMain")

from .database import engine
from .models import Base
from .data import load_game_settings
from . import routers as router_pkg

# -----------------------
# ⚙️ FastAPI Initialization
# -----------------------
app = FastAPI(
    title="Kingmaker's Rise API",
    version="6.13.2025.19.49",
    description="Backend for the Kingmakers Rise strategy MMO.",
)

# -----------------------
# 🔐 Middleware (CORS, security headers, etc.)
# -----------------------
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    origins = []  # Secure default when env var is missing
    logger.warning(
        "ALLOWED_ORIGINS not set; CORS disabled for external domains."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "online", "service": "Kingmaker's Rise API"}
