from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.rfq import RFQStatus
from ..models.user import User
from ..schemas.auction import DashboardStats
from ..schemas.rfq import RFQCreate, RFQOut, RFQUpdate
from ..services import rfq_service
from ..utils.dependencies import get_current_user, require_buyer

router = APIRouter(prefix="/api", tags=["rfqs"])


@router.post("/rfqs", response_model=RFQOut, status_code=201)
def create_rfq(
    data: RFQCreate,
    buyer: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    rfq = rfq_service.create_rfq(db, buyer, data)
    return rfq_service._enrich(db, rfq, buyer)


@router.get("/rfqs")
def list_rfqs(
    status: Optional[RFQStatus] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return rfq_service.list_rfqs(db, viewer, status, search, page, page_size)


@router.get("/rfqs/{rfq_id}", response_model=RFQOut)
def get_rfq(
    rfq_id: int,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rfq = rfq_service.get_rfq_or_404(db, rfq_id, viewer)
    return rfq_service._enrich(db, rfq, viewer)


@router.put("/rfqs/{rfq_id}", response_model=RFQOut)
def update_rfq(
    rfq_id: int,
    data: RFQUpdate,
    buyer: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    rfq = rfq_service.get_rfq_or_404(db, rfq_id, buyer)
    rfq = rfq_service.update_rfq(db, rfq, data)
    return rfq_service._enrich(db, rfq, buyer)


@router.delete("/rfqs/{rfq_id}", status_code=204)
def delete_rfq(
    rfq_id: int,
    buyer: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    rfq = rfq_service.get_rfq_or_404(db, rfq_id, buyer)
    rfq_service.delete_rfq(db, rfq)


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return rfq_service.dashboard_stats(db, viewer)
