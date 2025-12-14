from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class NotificationResponse(BaseModel):
    id: UUID
    userId: UUID
    type: str
    title: str
    message: str
    isRead: bool
    createdAt: datetime

    class Config:
        from_attributes = True
