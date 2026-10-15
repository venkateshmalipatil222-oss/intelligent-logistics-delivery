from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.enums import NotificationType, NotificationSeverity


class NotificationBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    message: str = Field(..., min_length=2)
    type: NotificationType = NotificationType.SYSTEM_ALERT
    severity: NotificationSeverity = NotificationSeverity.INFO
    delivery_id: Optional[int] = None
    order_id: Optional[int] = None
    metadata_json: Optional[str] = None


class NotificationCreate(NotificationBase):
    user_id: int


class NotificationResponse(NotificationBase):
    id: int
    user_id: int
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UnreadCountResponse(BaseModel):
    unread_count: int
