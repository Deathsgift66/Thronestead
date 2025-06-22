"""
Project: Thronestead ©
File: auth_middleware.py
Role: Authentication middleware.
Version: 2025-06-21
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class UserStateMiddleware(BaseHTTPMiddleware):
    """Attach a minimal user object with the JWT token to ``request.state``."""

    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split()[1]
        user_id = request.headers.get("X-User-ID")
        if token or user_id:
            request.state.user = type("User", (), {"token": token, "id": user_id})()
        response = await call_next(request)
        return response
