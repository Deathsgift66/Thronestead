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
import os
import re

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Optional environment configuration using python-dotenv
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - optional dependency
    print("python-dotenv not installed. Skipping .env loading.")


log_level = os.getenv("LOG_LEVEL")
logging.basicConfig(level=log_level if log_level else logging.INFO)
logger = logging.getLogger("Thronestead.BackendMain")

app = FastAPI(
    title="Thronestead API",
    version="6.13.2025.19.49",
    description="Backend for the Thronestead strategy MMO.",
)


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
    extra = os.getenv("ALLOWED_ORIGINS")
    origins = set(TRUSTED_ORIGINS) | {"http://localhost", "http://127.0.0.1"}
    if extra:
        origins.update(o.strip() for o in extra.split(",") if o.strip())
    return ["*"] if "*" in origins else list(origins)


origins = _build_cors_origins()

origin_regex = os.getenv(
    "ALLOWED_ORIGIN_REGEX", r"https:\/\/.*(thronestead\.com|netlify\.app)"
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
