import uuid

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    phone: str = Field(default="", max_length=50)
    email: str = Field(default="", max_length=320)
    address: str = ""
    notes: str = ""


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=320)
    address: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    phone: str
    email: str
    address: str
    notes: str
    is_active: bool
