from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auction_engine.closing import reconcile_rfq_status
from ..auction_engine.ranking import compute_rankings
from ..database import get_db
from ..models.activity_log import ActivityLog
from ..models.bid import Bid
from ..models.rfq import RFQ
from ..models.supplier_quote import SupplierQuote
from ..models.user import User
from ..schemas.auction import ActivityLogOut, AuctionStateOut
from ..services import rfq_service
from ..utils.dependencies import get_current_user

router = APIRouter(prefix="/api/rfqs/{rfq_id}", tags=["auction"])


@router.get("/auction", response_model=AuctionStateOut)
def auction_state(
    rfq_id: int,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rfq = rfq_service.get_rfq_or_404(db, rfq_id, viewer)
    rankings = compute_rankings(db, rfq_id)
    return {
        "rfq_id": rfq.id,
        "status": rfq.status,
        "bid_start_time": rfq.bid_start_time,
        "current_close_time": rfq.current_close_time,
        "forced_close_time": rfq.forced_close_time,
        "server_time": datetime.now(timezone.utc),
        "lowest_bid": rankings[0].amount if rankings else None,
        "l1_supplier_id": rankings[0].supplier_id if rankings else None,
        "total_bids": db.query(func.count(Bid.id)).filter(Bid.rfq_id == rfq_id).scalar() or 0,
        "supplier_count": db.query(func.count(SupplierQuote.id)).filter(
            SupplierQuote.rfq_id == rfq_id).scalar() or 0,
    }


@router.get("/status", response_model=AuctionStateOut)
def auction_status(
    rfq_id: int,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return auction_state(rfq_id, viewer, db)


@router.get("/activity", response_model=list[ActivityLogOut])
def activity(
    rfq_id: int,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rfq_service.get_rfq_or_404(db, rfq_id, viewer)
    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.rfq_id == rfq_id)
        .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .all()
    )
    return logs
