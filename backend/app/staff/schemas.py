import uuid

from pydantic import BaseModel, Field


class StaffProfileCreate(BaseModel):
    organization_id: uuid.UUID
    user_id: uuid.UUID
    staff_code: str = Field(min_length=1, max_length=50)
    phone: str = Field(default="", max_length=50)
    job_title: str = Field(default="", max_length=100)
    notes: str = ""


class StaffProfileResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    staff_code: str
    phone: str
    job_title: str
    notes: str
    is_active: bool
