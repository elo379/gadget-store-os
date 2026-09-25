from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


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
