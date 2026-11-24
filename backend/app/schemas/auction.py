from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from ..models.activity_log import ActivityEventType
from ..models.rfq import RFQStatus


class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rfq_id: int
    event_type: ActivityEventType
    message: str
    event_metadata: Optional[dict]
    supplier_id: Optional[int]
    created_at: datetime


class AuctionStateOut(BaseModel):
    rfq_id: int
    status: RFQStatus
    bid_start_time: datetime
    current_close_time: datetime
    forced_close_time: datetime
    server_time: datetime
    lowest_bid: Optional[Decimal] = None
    l1_supplier_id: Optional[int] = None
    total_bids: int = 0
    supplier_count: int = 0


class DashboardStats(BaseModel):
    total_rfqs: int = 0
    active_auctions: int = 0
    upcoming_auctions: int = 0
    closed_auctions: int = 0
    total_suppliers: int = 0
    total_bids: int = 0


class SupplierOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    company_name: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    quotes_count: int = 0
    bids_count: int = 0
