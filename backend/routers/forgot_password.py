# Project Name: Thronestead©
# File Name: forgot_password.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

import hashlib
import os
import time
import uuid
import re
import logging

from fastapi import APIRouter, HTTPException, Depends, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from pydantic import BaseModel, EmailStr

from ..supabase_client import get_supabase_client

from ..database import get_db
from backend.models import User, Notification
from services.audit_service import log_action


def send_email(to_email: str, subject: str, body: str) -> None:
    """Minimal email sending stub logging the intended message."""
    logging.getLogger("Thronestead.Email").info(
        "Sending email to %s with subject %s: %s", to_email, subject, body
    )

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ---------------------------------------------
# Configuration + In-memory Stores
# ---------------------------------------------
RESET_STORE: dict[str, tuple[str, float]] = {}  # token_hash: (user_id, expiry)
VERIFIED_SESSIONS: dict[str, tuple[str, float]] = {}  # user_id: (token_hash, expiry)
RATE_LIMIT: dict[str, list[float]] = {}  # IP: [timestamps]

TOKEN_TTL = int(os.getenv("PASSWORD_RESET_TOKEN_TTL", "900"))  # 15 minutes
SESSION_TTL = int(os.getenv("PASSWORD_RESET_SESSION_TTL", "600"))  # 10 minutes
RATE_LIMIT_MAX = int(os.getenv("PASSWORD_RESET_RATE_LIMIT", "3"))  # 3 per hour
