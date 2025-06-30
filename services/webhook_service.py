# Project Name: Thronestead©
# File Name: webhook_service.py
# Version: 6.14.2025.20.13
# Developer: Deathsgift66
"""Utility for sending webhooks with simple retry logic."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def send_webhook(url: str, payload: dict[str, Any], retries: int = 3) -> bool:
    """Send a webhook POST request with basic retries."""
    data = json.dumps(payload)
    for attempt in range(1, retries + 1):
        try:
            resp = httpx.post(url, content=data, headers={"Content-Type": "application/json"}, timeout=10.0)
            if resp.status_code < 400:
                return True
            logger.warning("Webhook %s failed with status %s", url, resp.status_code)
        except Exception as exc:  # pragma: no cover - network errors not deterministic
            logger.exception("Error sending webhook attempt %s: %s", attempt, exc)
        time.sleep(min(2 ** attempt, 60))
    return False
