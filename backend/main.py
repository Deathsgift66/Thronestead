# Project Name: Thronestead©
# File Name: main.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""FastAPI application for the Thronestead backend."""

if __name__ == "__main__" and __package__ is None:  # dev-only import fix
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "backend"

import logging
import os
import traceback
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import routers as router_pkg
from .auth_middleware import UserStateMiddleware
from .database import engine
from .models import Base

API_SECRET = os.getenv("API_SECRET")

# -----------------------
# ⚙️ FastAPI Initialization
# -----------------------
log_level = os.getenv("LOG_LEVEL")
logging.basicConfig(level=log_level if log_level else logging.INFO)
logger = logging.getLogger("Thronestead.BackendMain")

app = FastAPI(
    title="Thronestead API",
    version="6.13.2025.19.49",
    description="Backend for the Thronestead strategy MMO.",
)

# -----------------------
# 🔐 CORS Middleware
# -----------------------
origins = [
    "https://thronestead.com",
    "https://www.thronestead.com",
]

extra_origins = os.getenv("ALLOWED_ORIGINS")
if extra_origins:
    origins.extend(o.strip() for o in extra_origins.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(UserStateMiddleware)

# -----------------------
# 🗃️ Ensure Database Tables Exist
# -----------------------
if engine:
    Base.metadata.create_all(bind=engine)

# -----------------------
# ⚙️ Load Global Game Settings
# -----------------------
try:
    from . import data

    data.load_game_settings()
    logger.info("✅ Loaded game settings.")
except Exception as e:
    logger.exception("❌ Crash during startup loading game settings: %s", e)
    traceback.print_exc()
    raise

# -----------------------
# 📦 Auto-load Routers Safely
# -----------------------
for name in router_pkg.__all__:
    try:
        module = getattr(router_pkg, name)
        router_obj = getattr(module, "router", None)
        if router_obj:
            app.include_router(router_obj)
        alt_obj = getattr(module, "alt_router", None)
        if alt_obj:
            app.include_router(alt_obj)
    except Exception as e:
        logger.exception(f"❌ Failed to import or include router '{name}': {e}")
        raise

# -----------------------
# 🖼️ Static File Serving (Frontend SPA)
# -----------------------
_frontend = os.getenv("FRONTEND_DIR")
BASE_DIR = Path(_frontend) if _frontend else Path(__file__).resolve().parent.parent
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")


# -----------------------
# ✅ Health Check Endpoint
# -----------------------
@app.get("/health-check")
def health_check():
    return {"status": "online", "service": "Thronestead API"}


# -----------------------
# 🧪 Run App Locally (Dev Only)
# -----------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
