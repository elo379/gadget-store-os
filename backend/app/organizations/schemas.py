from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    slug: str = Field(min_length=2, max_length=100)
    owner_email: EmailStr | None = None
    owner_password: str | None = Field(default=None, min_length=8, max_length=128)
    activation_code: str = Field(min_length=24, max_length=24)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    is_active: bool


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    user_id: UUID
    role_name: str
    personnel_id: str | None
    is_owner: bool
    is_active: bool


class OrganizationMemberResponse(BaseModel):
    user_id: UUID
    email: EmailStr
    role_name: str
    personnel_id: str | None
    is_owner: bool
    is_active: bool
