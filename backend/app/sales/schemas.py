import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class SaleLineCreate(BaseModel):
    product_id: uuid.UUID
    location_id: uuid.UUID | None = None
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    device_id: uuid.UUID | None = None


class SaleCreate(BaseModel):
    organization_id: uuid.UUID
    customer_id: uuid.UUID | None = None
    sold_by_user_id: uuid.UUID | None = None
    reference_number: str = Field(min_length=1, max_length=100)
    discount: Decimal = Field(ge=0, default=Decimal("0"))
    tax: Decimal = Field(ge=0, default=Decimal("0"))
    fees: Decimal = Field(ge=0, default=Decimal("0"))
    payment_method: str | None = Field(default=None, max_length=50)
    amount_paid: Decimal = Field(ge=0, default=Decimal("0"))
    payment_reference: str = ""
    lines: list[SaleLineCreate] = Field(min_length=1)
    notes: str = ""


class SalePaymentCreate(BaseModel):
    sale_id: uuid.UUID
    payment_method: str = Field(min_length=1, max_length=50)
    amount: Decimal = Field(gt=0)
    reference: str = ""
    notes: str = ""


class SaleLineResponse(BaseModel):
    id: uuid.UUID
    sale_id: uuid.UUID
    product_id: uuid.UUID
    device_id: uuid.UUID | None
    quantity: Decimal
    unit_price: Decimal
    unit_cost: Decimal
    line_total: Decimal
    line_cogs: Decimal


class SalePaymentResponse(BaseModel):
    id: uuid.UUID
    sale_id: uuid.UUID
    payment_method: str
    amount: Decimal
    reference: str
    notes: str


class SaleResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    customer_id: uuid.UUID | None
    sold_by_user_id: uuid.UUID | None
    reference_number: str
    status: str
    payment_status: str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")
    total: Decimal
    cogs: Decimal
    gross_profit: Decimal
    notes: str
    lines: list[SaleLineResponse]
    payments: list[SalePaymentResponse]


class SaleReceiptResponse(BaseModel):
    sale_id: uuid.UUID
    reference_number: str
    status: str
    payment_status: str
    customer_id: uuid.UUID | None
    sold_by_user_id: uuid.UUID | None
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    cogs: Decimal
    gross_profit: Decimal
    lines: list[SaleLineResponse]


class SalesSummaryResponse(BaseModel):
    sales_count: int
    revenue: Decimal
    cogs: Decimal
    gross_profit: Decimal
