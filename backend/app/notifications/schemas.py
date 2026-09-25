import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    organization_id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str = Field(
        min_length=1,
        max_length=50,
    )
    title: str = Field(
        min_length=1,
        max_length=200,
    )
    message: str
    reference_type: str = ""
    reference_id: uuid.UUID | None = None


class NotificationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    notification_type: str
    title: str
    message: str
    reference_type: str
    reference_id: uuid.UUID | None
    is_read: bool
    is_active: bool
    created_at: datetime
