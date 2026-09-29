from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal


class ProductCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(default="", max_length=2000)


class ProductCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    description: str
    is_active: bool


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    sku: str = Field(min_length=1, max_length=100)
    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=150)
    description: str = Field(default="", max_length=2000)
    category_id: UUID | None = None
    is_serialized: bool = False
    product_type: str = Field(default="other", pattern="^(smartphone|laptop|tablet|accessory|screen_protector|charger_cable|wearable|audio|other)$")
    barcode: str = Field(default="", max_length=150)
    unit_cost: Decimal = Field(default=Decimal("0"), ge=0)
    selling_price: Decimal = Field(default=Decimal("0"), ge=0)
    reorder_threshold: Decimal = Field(default=Decimal("0"), ge=0)


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    category_id: UUID | None
    name: str
    sku: str
    brand: str
    model: str
    description: str
    is_serialized: bool
    is_active: bool
    product_type: str
    barcode: str
    unit_cost: Decimal
    selling_price: Decimal
    reorder_threshold: Decimal
