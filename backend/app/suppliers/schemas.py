import uuid

from pydantic import BaseModel, ConfigDict, Field


class SupplierCreate(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    notes: str = ""


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    contact_person: str
    phone: str
    email: str
    address: str
    notes: str
    is_active: bool
