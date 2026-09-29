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


class InvitationCreatedResponse(InvitationResponse):
    # Returned once to the creator so it can be shared with the invitee.
    activation_id: uuid.UUID
    activation_credential: str


class InvitationAccept(BaseModel):
    activation_id: uuid.UUID
    token: str = Field(min_length=20)
    password: str = Field(min_length=8)


class InvitationAcceptResponse(BaseModel):
    membership_id: uuid.UUID
    personnel_id: str
    role_name: str
    account_status: str
