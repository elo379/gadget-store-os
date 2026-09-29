import uuid
from decimal import Decimal

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


class CustomerReturnLineCreate(BaseModel):
    sale_line_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    location_id: uuid.UUID | None = None
    condition: str = "unknown"
    disposition: str = "RESTOCK"


class CustomerReturnCreate(BaseModel):
    organization_id: uuid.UUID
    sale_id: uuid.UUID
    reference_number: str = Field(min_length=1, max_length=100)
    reason: str = ""
    lines: list[CustomerReturnLineCreate] = Field(min_length=1)


class CustomerReturnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    sale_id: uuid.UUID
    customer_id: uuid.UUID | None
    seller_user_id: uuid.UUID | None = None
    reference_number: str
    reason: str
    refund_amount: Decimal
    status: str
    lines: list["CustomerReturnLineResponse"]


class CustomerReturnLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sale_line_id: uuid.UUID
    quantity: Decimal
    amount: Decimal
    reason: str
    condition: str = "unknown"
    disposition: str = "RESTOCK"
    original_cost: Decimal = Decimal("0")
