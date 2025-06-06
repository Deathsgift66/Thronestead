from fastapi import APIRouter

router = APIRouter(prefix="/api/audit-log", tags=["audit_log"])


@router.get("")
async def audit_log():
    return {"logs": []}

