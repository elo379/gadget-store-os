import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class InvitationCreate(BaseModel):
    email: EmailStr
    role_name: str


class InvitationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    role_name: str
    status: str
    expires_at: datetime


class InvitationAccept(BaseModel):
    token: str = Field(min_length=20)
    password: str = Field(min_length=8)


class InvitationAcceptResponse(BaseModel):
    membership_id: uuid.UUID
    personnel_id: str
    role_name: str
    account_status: str
