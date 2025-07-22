# Project Name: Thronestead©
# File Name: main.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""FastAPI application for the Thronestead backend."""

if __name__ == "__main__" and __package__ is None:  # dev-only import fix
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent.parent))
    __package__ = "backend"

import logging
import traceback
from pathlib import Path

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import routers as router_pkg
from .rate_limiter import setup_rate_limiter
from . import database
from .models import Base
from .env_utils import get_env_var
from backend.routers import auth

# Optional environment configuration using python-dotenv
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - optional dependency
    print("python-dotenv not installed. Skipping .env loading.")

# Ensure the database uses values from the loaded .env file
database.init_engine()


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
        response = JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    else:
        response = JSONResponse({"detail": "Internal Server Error"}, status_code=500)
    return _maybe_add_cors_headers(request, response)


# -----------------------
# 🔐 CORS Middleware
# -----------------------
# Default allowed origins including local development and production URLs.
TRUSTED_ORIGINS = [
    "https://thronestead.com",
    "https://www.thronestead.com",
    "https://thronestead.com/",
    "https://www.thronestead.com/",
    "https://thronestead.netlify.app",
    "https://thronestead.netlify.app/",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _build_cors_origins() -> list[str]:
    extra = get_env_var("ALLOWED_ORIGINS")
    origins = set(TRUSTED_ORIGINS) | {"http://localhost", "http://127.0.0.1"}
    if extra:
        origins.update(o.strip() for o in extra.split(",") if o.strip())
    return ["*"] if "*" in origins else list(origins)


origins = _build_cors_origins()

origin_regex = get_env_var(
    "ALLOWED_ORIGIN_REGEX", default=r"https:\/\/.*(thronestead\.com|netlify\.app)"
)

# Apply the CORS middleware before other custom middleware so that CORS
# headers are always included in the response.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility to apply CORS headers to custom responses (e.g., error handler)
import re

_origin_pattern = re.compile(origin_regex) if origin_regex else None


def _maybe_add_cors_headers(request: Request, response: Response) -> Response:
    """Attach CORS headers when the request origin is permitted."""
    origin = request.headers.get("origin")
    if not origin:
        return response
    if "*" in origins:
        response.headers.setdefault("Access-Control-Allow-Origin", "*")
        response.headers.setdefault("Access-Control-Allow-Credentials", "true")
    elif origin in origins or (_origin_pattern and _origin_pattern.match(origin)):
        response.headers.setdefault("Access-Control-Allow-Origin", origin)
        response.headers.setdefault("Access-Control-Allow-Credentials", "true")
    return response


# Print configured origins during startup for debugging purposes.
@app.on_event("startup")
async def _cors_startup_log() -> None:
    logger.info("\u2705 CORS configured for: %s", ", ".join(origins))


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

ROUTER_ATTRS = ("router", "alt_router", "custom_router")


def _include_routers() -> None:
    for name in router_pkg.__all__:
        if name == "auth":
            continue
        try:
            module = getattr(router_pkg, name)
            router = next(
                (
                    getattr(module, attr)
                    for attr in ROUTER_ATTRS
                    if getattr(module, attr, None)
                ),
                None,
            )
            if router:
                app.include_router(router)
        except Exception as exc:
            logger.exception(
                "❌ Failed to import or include router '%s': %s", name, exc
            )
            FAILED_ROUTERS.append(name)


_include_routers()
# Auth router already defines its own prefix
app.include_router(auth.router)

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

    port = int(get_env_var("PORT", default="8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
