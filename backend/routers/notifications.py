from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationAction(BaseModel):
    notification_id: str | None = None


@router.get("/list")
async def list_notifications():
    return {"notifications": []}


@router.post("/mark_read")
async def mark_read(payload: NotificationAction):
    return {"message": "Marked read", "id": payload.notification_id}


@router.post("/mark_all_read")
async def mark_all_read():
    return {"message": "All marked read"}


@router.post("/clear_all")
async def clear_all():
    return {"message": "All cleared"}

