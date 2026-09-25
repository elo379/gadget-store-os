from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class InventoryLocationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str = Field(default="", max_length=2000)


class InventoryLocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str
    is_active: bool


class InventoryItemCreate(BaseModel):
    product_id: UUID
    location_id: UUID | None = None
    quantity: Decimal = Field(default=Decimal("0"), ge=0)
    notes: str = Field(default="", max_length=2000)


class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    product_id: UUID
    location_id: UUID | None
    quantity: Decimal
    reserved_quantity: Decimal
    status: str
    notes: str


class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    inventory_item_id: UUID
    movement_type: str
    quantity: Decimal
    quantity_before: Decimal
    quantity_after: Decimal
    reference_type: str | None
    reference_id: UUID | None
    reason: str
    performed_by_user_id: UUID | None
