import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class FinancialTransactionCreate(BaseModel):
    organization_id: uuid.UUID
    transaction_type: str = Field(min_length=1, max_length=50)
    direction: str = Field(min_length=1, max_length=20)
    amount: Decimal = Field(gt=0)
    reference_type: str = ""
    reference_id: uuid.UUID | None = None
    description: str = ""


class FinancialSummaryResponse(BaseModel):
    revenue: Decimal
    cogs: Decimal
    gross_profit: Decimal
    expenses: Decimal
    operating_result: Decimal
    payments_received: Decimal
    customer_outstanding: Decimal
