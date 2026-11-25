from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auction_engine.engine import BidValidationError
from ..auction_engine.ranking import compute_rankings
from ..database import get_db
from ..models.bid import Bid
from ..models.rfq import RFQ, RFQStatus
from ..models.supplier import Supplier
from ..models.user import User, UserRole
from ..schemas.bid import BidCreate, BidHistoryEntry, BidOut, RankingEntry
from ..services import bidding_service, rfq_service
from ..utils.dependencies import get_current_user, require_supplier
from ..websocket.events import rankings_payload
from ..websocket.manager import broadcast_threadsafe

router = APIRouter(prefix="/api/rfqs/{rfq_id}", tags=["bids"])


@router.post("/bids", response_model=BidOut, status_code=201)
def submit_bid(
    rfq_id: int,
    data: BidCreate,
    supplier: Supplier = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    try:
        result = bidding_service.submit_bid(db, rfq_id, supplier, data.amount)
    except BidValidationError as e:
        raise HTTPException(e.status_code, e.message)
    bid = result.bid

    # Broadcast AFTER commit
    broadcast_threadsafe(rfq_id, "new_bid", {
        "bid_id": bid.id,
        "supplier_id": supplier.id,
        "supplier_name": supplier.company_name or supplier.user.full_name,
        "amount": bid.amount,
        "created_at": bid.created_at,
        "lowest_bid": result.lowest_bid,
        "l1_supplier_id": result.l1_supplier_id,
    })
    broadcast_threadsafe(rfq_id, "rankings", {
        "rankings": rankings_payload(result.rankings_after),
    })
    if result.extension.extended:
        broadcast_threadsafe(rfq_id, "auction_extended", {
            "reason": result.extension.reason,
            "previous_close_time": result.extension.previous_close_time,
            "new_close_time": result.extension.new_close_time,
        })
    return {
        "id": bid.id, "rfq_id": bid.rfq_id, "supplier_id": bid.supplier_id,
        "supplier_name": supplier.company_name or supplier.user.full_name,
        "amount": bid.amount, "created_at": bid.created_at,
    }


@router.get("/bids", response_model=list[BidHistoryEntry])
def list_bids(
    rfq_id: int,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rfq = rfq_service.get_rfq_or_404(db, rfq_id, viewer)
    history = bidding_service.get_bid_history(db, rfq_id)
    if viewer.role == UserRole.SUPPLIER:
        # suppliers see amounts/history but only own supplier name details stay
        pass
    return history


@router.get("/my-bids", response_model=list[BidOut])
def my_bids(
    rfq_id: int,
    supplier: Supplier = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    rfq_service.get_rfq_or_404(db, rfq_id, supplier.user)
    bids = (
        db.query(Bid)
        .filter(Bid.rfq_id == rfq_id, Bid.supplier_id == supplier.id)
        .order_by(Bid.created_at.desc())
        .all()
    )
    name = supplier.company_name or supplier.user.full_name
    return [{
        "id": b.id, "rfq_id": b.rfq_id, "supplier_id": b.supplier_id,
        "supplier_name": name, "amount": b.amount, "created_at": b.created_at,
    } for b in bids]


@router.get("/rankings", response_model=list[RankingEntry])
def rankings(
    rfq_id: int,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rfq_service.get_rfq_or_404(db, rfq_id, viewer)
    viewer_sid = (
        viewer.supplier_profile.id
        if viewer.role == UserRole.SUPPLIER and viewer.supplier_profile else None
    )
    return rankings_payload(compute_rankings(db, rfq_id), viewer_sid)
