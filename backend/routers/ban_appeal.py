"""API routes for ban appeals."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from ..env_utils import get_env_var
import logging

from services.email_service import send_email
from .signup import verify_hcaptcha

router = APIRouter(prefix="/api/ban", tags=["ban"])
logger = logging.getLogger("Thronestead.BanAppeal")
BAN_APPEAL_EMAIL = get_env_var("BAN_APPEAL_EMAIL", "thronestead@gmail.com")


class AppealPayload(BaseModel):
    email: EmailStr
    message: str
    captcha_token: str | None = None


@router.post("/appeal")
async def submit_appeal(payload: AppealPayload, request: Request):
    if len(payload.message.strip()) < 10:
        raise HTTPException(status_code=400, detail="Appeal message too short")
    if not verify_hcaptcha(
        payload.captcha_token,
        request.client.host if request.client else None,
    ):
        raise HTTPException(status_code=400, detail="Captcha verification failed")

    body = (
        f"From: {payload.email}\n"
        f"IP: {request.client.host if request.client else 'unknown'}\n\n"
        f"{payload.message}"
    )
    try:
        send_email(BAN_APPEAL_EMAIL, "Ban Appeal", body)
    except Exception as exc:  # pragma: no cover - email sending may fail
        logger.exception("Failed to send ban appeal email: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to submit appeal")
    return {"status": "received"}
