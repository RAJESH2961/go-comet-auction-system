from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class QuoteCreate(BaseModel):
    carrier_name: str = Field(min_length=1, max_length=300)
    freight_charges: Decimal = Field(ge=0)
    origin_charges: Decimal = Field(ge=0)
    destination_charges: Decimal = Field(ge=0)
    transit_time: Optional[str] = None
    validity_of_quote: Optional[datetime] = None


class QuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfq_id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    carrier_name: str
    freight_charges: Decimal
    origin_charges: Decimal
    destination_charges: Decimal
    total_amount: Decimal
    transit_time: Optional[str]
    validity_of_quote: Optional[datetime]
    created_at: datetime
