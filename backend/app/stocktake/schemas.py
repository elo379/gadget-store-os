import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class StocktakeCreate(BaseModel):
    organization_id: uuid.UUID
    location_id: uuid.UUID | None = None
    reference_number: str = Field(
        min_length=1,
        max_length=100,
    )
    notes: str = ""


class StocktakeCount(BaseModel):
    counted_quantity: Decimal = Field(ge=0)
    notes: str = ""


class StocktakeLineResponse(BaseModel):
    id: uuid.UUID
    stocktake_id: uuid.UUID
    inventory_item_id: uuid.UUID
    expected_quantity: Decimal
    counted_quantity: Decimal | None
    variance: Decimal
    notes: str


class StocktakeResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    location_id: uuid.UUID | None
    reference_number: str
    status: str
    notes: str
