from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BidCreate(BaseModel):
    amount: Decimal = Field(gt=0)


class BidOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfq_id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    amount: Decimal
    created_at: datetime


class RankingEntry(BaseModel):
    rank: int
    rank_label: str
    supplier_id: int
    supplier_name: str
    company_name: Optional[str] = None
    latest_bid: Decimal
    transit_time: Optional[str] = None
    bid_time: datetime
    is_me: bool = False


class BidHistoryEntry(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    amount: Decimal
    previous_amount: Optional[Decimal] = None
    created_at: datetime
