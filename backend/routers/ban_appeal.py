"""API routes for ban appeals."""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from services.email_service import send_email
from .signup import verify_hcaptcha

router = APIRouter(prefix="/api/ban", tags=["ban"])


class AppealPayload(BaseModel):
    email: EmailStr
    message: str
    captcha_token: str | None = None


@router.post("/appeal")
async def submit_appeal(payload: AppealPayload, request: Request):
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
    send_email("thronestead@gmail.com", "Ban Appeal", body)
    return {"status": "received"}
