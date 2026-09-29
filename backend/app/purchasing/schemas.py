import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PurchaseLineCreate(BaseModel):
    product_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    unit_cost: Decimal = Field(ge=0)


class PurchaseOrderCreate(BaseModel):
    organization_id: uuid.UUID
    supplier_id: uuid.UUID
    reference_number: str = Field(min_length=1, max_length=100)
    lines: list[PurchaseLineCreate] = Field(min_length=1)
    notes: str = ""


class PurchaseLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    purchase_id: uuid.UUID
    product_id: uuid.UUID
    quantity: Decimal
    unit_cost: Decimal
    line_total: Decimal


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    supplier_id: uuid.UUID
    reference_number: str
    status: str
    subtotal: Decimal
    total: Decimal
    notes: str
    lines: list[PurchaseLineResponse]


class SupplierTransactionCreate(BaseModel):
    organization_id: uuid.UUID
    supplier_id: uuid.UUID
    transaction_type: str = Field(min_length=1, max_length=50)
    amount: Decimal = Field(gt=0)
    reference_type: str = ""
    reference_id: uuid.UUID | None = None
    notes: str = ""


class SupplierTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    supplier_id: uuid.UUID
    transaction_type: str
    amount: Decimal
    reference_type: str
    reference_id: uuid.UUID | None
    notes: str


class PurchaseReceiveLine(BaseModel):
    purchase_line_id: uuid.UUID
    quantity: Decimal = Field(gt=0)
    location_id: uuid.UUID | None = None
    imei: str | None = None
    imei_2: str | None = None
    serial_number: str | None = None
    barcode: str | None = None
    brand: str = ""
    model: str = ""
    variant: str = ""
    storage: str = ""
    ram: str = ""
    color: str = ""
    network_sim: str = ""
    grade: str = ""
    selling_price: Decimal | None = Field(default=None, ge=0)
    warranty: str = ""
    condition: str = "new"
    notes: str = ""


class PurchaseReceiveRequest(BaseModel):
    organization_id: uuid.UUID
    received_by_user_id: uuid.UUID | None = None
    lines: list[PurchaseReceiveLine] = Field(min_length=1)
