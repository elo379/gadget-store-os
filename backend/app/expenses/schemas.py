import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class ExpenseCategoryCreate(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(min_length=1, max_length=150)
    description: str = ""


class ExpenseCreate(BaseModel):
    organization_id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal = Field(gt=0)
    payment_method: str = Field(default="", max_length=50)
    reference_number: str = Field(min_length=1, max_length=100)
    description: str = ""


class ExpenseResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal
    payment_method: str
    reference_number: str
    description: str
    status: str
