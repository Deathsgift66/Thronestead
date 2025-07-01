# Comment
# Project Name: Thronestead©
# File Name: main.py
# Version: 7/1/2025 10:31
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

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import routers as router_pkg
from .rate_limiter import setup_rate_limiter
from . import database
from .models import Base
from .env_utils import get_env_var

# Optional environment configuration using python-dotenv
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - optional dependency
    print("python-dotenv not installed. Skipping .env loading.")

# Ensure the database uses values from the loaded .env file
database.init_engine()

API_SECRET = get_env_var("API_SECRET")

# Load Supabase credentials for downstream modules
SUPABASE_URL = get_env_var("SUPABASE_URL")
SUPABASE_KEY = get_env_var("SUPABASE_ANON_KEY") or get_env_var("SUPABASE_SERVICE_ROLE_KEY")

# -----------------------
# ⚙️ FastAPI Initialization
# -----------------------
log_level = get_env_var("LOG_LEVEL")
logging.basicConfig(level=log_level if log_level else logging.INFO)
logger = logging.getLogger("Thronestead.BackendMain")

app = FastAPI(
    title="Thronestead API",
    version="6.13.2025.19.49",
    description="Backend for the Thronestead strategy MMO.",
)

setup_rate_limiter(app)


# -----------------------
# 🌐 Global Error Handling
# -----------------------

@app.exception_handler(Exception)
async def _unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    if isinstance(exc, HTTPException):
        # Preserve HTTPException status codes for well-formed API responses
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    return JSONResponse({"detail": "Internal Server Error"}, status_code=500)

# -----------------------
# 🔐 CORS Middleware
# -----------------------
# Default allowed origins including local development and production URLs.
origins = [
    "https://thronestead.com",
    "https://www.thronestead.com",
    "https://thronestead.com/",
    "https://www.thronestead.com/",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://127.0.0.1",
]

# Allow additional origins via environment variable
extra_origins = get_env_var("ALLOWED_ORIGINS")
if extra_origins:
    origins.extend(o.strip() for o in extra_origins.split(",") if o.strip())

origin_regex = r"https:\/\/(?:.*thronestead\.com|thronestead\.onrender\.com)"
env_regex = get_env_var("ALLOWED_ORIGIN_REGEX")
if env_regex:
    origin_regex = env_regex

allow_credentials = True
if "*" in origins:
    origins = ["*"]
    # Credentials are still allowed even when wildcard origins are permitted.

# Apply the CORS middleware before other custom middleware so that CORS
# headers are always included in the response.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Print configured origins during startup for debugging purposes.
@app.on_event("startup")
async def _cors_startup_log() -> None:
    logger.info("\u2705 CORS configured for:")
    for origin in origins:
        logger.info(" - %s", origin)

# -----------------------
# 🗃️ Ensure Database Tables Exist
# -----------------------
if database.engine:
    Base.metadata.create_all(bind=database.engine)

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
    # Continue with partially initialized settings

# -----------------------
# 📦 Auto-load Routers Safely
# -----------------------
FAILED_ROUTERS: list[str] = []

for name in router_pkg.__all__:
    if name == "auth":
        continue
    try:
        module = getattr(router_pkg, name)
        router_obj = getattr(module, "router", None)
        if router_obj:
            app.include_router(router_obj)
        alt_obj = getattr(module, "alt_router", None)
        if alt_obj:
            app.include_router(alt_obj)
        custom_obj = getattr(module, "custom_router", None)
        if custom_obj:
            app.include_router(custom_obj)
    except Exception as e:
        logger.exception("❌ Failed to import or include router '%s': %s", name, e)
        FAILED_ROUTERS.append(name)

from backend.routers import auth
app.include_router(auth.router, prefix="/api/auth")

# -----------------------
# 🖼️ Static File Serving (Frontend SPA)
# -----------------------
_frontend = get_env_var("FRONTEND_DIR")
BASE_DIR = Path(_frontend) if _frontend else Path(__file__).resolve().parent.parent
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")


# -----------------------
# ✅ Health Check Endpoint
# -----------------------
@app.get("/health-check")
def health_check():
    return {
        "status": "online",
        "service": "Thronestead API",
        "failedRouters": FAILED_ROUTERS,
    }


# -----------------------
# 🧪 Run App Locally (Dev Only)
# -----------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
