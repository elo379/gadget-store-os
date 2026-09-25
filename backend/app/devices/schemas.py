import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DeviceRecordCreate(BaseModel):
    product_id: uuid.UUID | None = None

    imei: str | None = Field(default=None, max_length=15)
    imei_2: str | None = Field(default=None, max_length=15)
    serial_number: str | None = Field(default=None, max_length=150)
    barcode: str | None = Field(default=None, max_length=150)

    brand: str = Field(default="", max_length=100)
    model: str = Field(default="", max_length=150)
    variant: str = Field(default="", max_length=150)
    storage: str = Field(default="", max_length=50)
    color: str = Field(default="", max_length=75)

    source_type: str = Field(default="vendor", max_length=50)
    source_name: str = Field(default="", max_length=200)
    source_contact: str = Field(default="", max_length=150)
    source_reference: str = Field(default="", max_length=150)

    received_by_user_id: uuid.UUID | None = None

    condition: str = Field(default="unknown", max_length=50)
    status: str = Field(default="received", max_length=50)

    acquisition_cost: Decimal | None = None

    notes: str = ""


class DeviceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID

    product_id: uuid.UUID | None

    imei: str | None
    imei_2: str | None
    serial_number: str | None
    barcode: str | None

    brand: str
    model: str
    variant: str
    storage: str
    color: str

    source_type: str
    source_name: str
    source_contact: str
    source_reference: str

    received_by_user_id: uuid.UUID | None

    condition: str
    status: str

    acquisition_cost: Decimal | None

    notes: str
    is_active: bool
