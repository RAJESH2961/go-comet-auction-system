from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..models.auction_config import TriggerType
from ..models.rfq import RFQStatus


class AuctionConfigIn(BaseModel):
    trigger_window_minutes: int = Field(gt=0, le=1440)
    extension_duration_minutes: int = Field(gt=0, le=1440)
    trigger_type: TriggerType


class RFQCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    reference_id: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    pickup_location: Optional[str] = None
    destination_location: Optional[str] = None
    service_date: Optional[datetime] = None
    bid_start_time: datetime
    bid_close_time: datetime
    forced_close_time: datetime
    auction_config: AuctionConfigIn

    @model_validator(mode="after")
    def validate_times(self):
        if self.bid_start_time >= self.bid_close_time:
            raise ValueError("bid_start_time must be before bid_close_time")
        if self.forced_close_time <= self.bid_close_time:
            raise ValueError("forced_close_time must be later than bid_close_time")
        return self


class RFQUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=300)
    description: Optional[str] = None
    pickup_location: Optional[str] = None
    destination_location: Optional[str] = None
    service_date: Optional[datetime] = None
    bid_start_time: Optional[datetime] = None
    bid_close_time: Optional[datetime] = None
    forced_close_time: Optional[datetime] = None
    auction_config: Optional[AuctionConfigIn] = None


class AuctionConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trigger_window_minutes: int
    extension_duration_minutes: int
    trigger_type: TriggerType


class RFQOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    buyer_id: int
    name: str
    reference_id: str
    description: Optional[str]
    pickup_location: Optional[str]
    destination_location: Optional[str]
    service_date: Optional[datetime]
    bid_start_time: datetime
    bid_close_time: datetime
    current_close_time: datetime
    forced_close_time: datetime
    status: RFQStatus
    created_at: datetime
    auction_config: Optional[AuctionConfigOut] = None
    lowest_bid: Optional[Decimal] = None
    supplier_count: int = 0
    bid_count: int = 0
    has_my_quote: bool = False
    has_participated: bool = False
