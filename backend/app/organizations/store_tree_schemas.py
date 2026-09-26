import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StoreTreePolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    managers_can_create_staff: bool
    managers_can_create_managers: bool
    managers_can_assign_roles: bool
    managers_can_modify_permissions: bool


class StoreTreePolicyUpdate(BaseModel):
    managers_can_create_staff: bool = False
    managers_can_create_managers: bool = False
    managers_can_assign_roles: bool = False
    managers_can_modify_permissions: bool = False


class PersonnelCreate(BaseModel):
    email: str
    password: str = Field(min_length=8)
    role_name: str


class StoreTreeMember(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    personnel_id: str | None
    role_name: str
    parent_membership_id: uuid.UUID | None
    created_by_membership_id: uuid.UUID | None
    account_status: str
    invited_at: datetime | None
    accepted_at: datetime | None
    is_owner: bool
    is_active: bool


class StoreTreeResponse(BaseModel):
    organization_id: uuid.UUID
    members: list[StoreTreeMember]
