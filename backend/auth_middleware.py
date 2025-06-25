"""Middleware for decoding JWTs and injecting user context."""

import logging
import os
from typing import Any, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .database import SessionLocal
from jose import jwt
from sqlalchemy import text


logger = logging.getLogger("Thronestead.AuthMiddleware")


class UserStateMiddleware(BaseHTTPMiddleware):
    """Decode the JWT and attach a user object for downstream use."""

    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split()[1]

        claims: dict[str, Any] | None = None
        auth_user_id: Optional[str] = None
        if token:
            try:
                secret = os.getenv("SUPABASE_JWT_SECRET")
                if secret:
                    claims = jwt.decode(token, secret, algorithms=["HS256"])
                else:
                    claims = jwt.decode(token, options={"verify_signature": False})
                auth_user_id = claims.get("sub")
            except Exception:  # pragma: no cover - invalid tokens shouldn't crash
                logger.exception("Failed to decode JWT token")

        if not auth_user_id:
            auth_user_id = request.headers.get("X-User-ID")

        user_id = None
        setup_complete = False
        if auth_user_id and SessionLocal is not None:
            try:
                with SessionLocal() as db:
                    row = db.execute(
                        text(
                            "SELECT user_id, auth_user_id, setup_complete "
                            "FROM users WHERE user_id = :uid"
                        ),
                        {"uid": auth_user_id},
                    ).fetchone()
                    if row:
                        user_id = str(row[0])
                        auth_user_id = str(row[1] or row[0])
                        setup_complete = bool(row[2])
            except Exception:  # pragma: no cover - DB errors shouldn't block
                logger.exception("Failed to load user context")

        if auth_user_id or user_id:
            user_obj = type(
                "User",
                (),
                {
                    "token": token,
                    "id": user_id or auth_user_id,
                    "auth_id": auth_user_id,
                    "claims": claims or {},
                    "setup_complete": setup_complete,
                },
            )()
            request.state.user = user_obj
            request.app.current_user = user_obj

        response = await call_next(request)
        return response
