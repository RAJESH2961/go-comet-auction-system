from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auction_engine.closing import reconcile_rfq_status
from ..models.activity_log import ActivityLog, ActivityEventType
from ..models.auction_config import AuctionConfig
from ..models.bid import Bid
from ..models.rfq import RFQ, RFQStatus
from ..models.supplier import Supplier
from ..models.supplier_quote import SupplierQuote
from ..models.user import User, UserRole
from ..schemas.rfq import RFQCreate, RFQUpdate


def _enrich(db: Session, rfq: RFQ, viewer: User | None = None) -> dict:
    """Attach computed fields used in list/detail responses."""
    lowest = (
        db.query(func.min(Bid.amount)).filter(Bid.rfq_id == rfq.id).scalar()
    )
    if lowest is None:
        q = db.query(func.min(SupplierQuote.total_amount)).filter(
            SupplierQuote.rfq_id == rfq.id
        ).scalar()
        lowest = q
    supplier_count = db.query(func.count(SupplierQuote.id)).filter(
        SupplierQuote.rfq_id == rfq.id
    ).scalar() or 0
    bid_count = db.query(func.count(Bid.id)).filter(Bid.rfq_id == rfq.id).scalar() or 0

    has_my_quote = False
    has_participated = False
    if viewer and viewer.role == UserRole.SUPPLIER and viewer.supplier_profile:
        sid = viewer.supplier_profile.id
        has_my_quote = db.query(SupplierQuote).filter(
            SupplierQuote.rfq_id == rfq.id, SupplierQuote.supplier_id == sid
        ).first() is not None
        has_participated = has_my_quote or db.query(Bid).filter(
            Bid.rfq_id == rfq.id, Bid.supplier_id == sid
        ).first() is not None

    out = {
        "id": rfq.id, "buyer_id": rfq.buyer_id, "name": rfq.name,
        "reference_id": rfq.reference_id, "description": rfq.description,
        "pickup_location": rfq.pickup_location,
        "destination_location": rfq.destination_location,
        "service_date": rfq.service_date,
        "bid_start_time": rfq.bid_start_time,
        "bid_close_time": rfq.bid_close_time,
        "current_close_time": rfq.current_close_time,
        "forced_close_time": rfq.forced_close_time,
        "status": rfq.status, "created_at": rfq.created_at,
        "auction_config": rfq.auction_config,
        "lowest_bid": lowest,
        "supplier_count": supplier_count,
        "bid_count": bid_count,
        "has_my_quote": has_my_quote,
        "has_participated": has_participated,
    }
    return out


def create_rfq(db: Session, buyer: User, data: RFQCreate) -> RFQ:
    if db.query(RFQ).filter(RFQ.reference_id == data.reference_id).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "RFQ reference ID already exists")
    rfq = RFQ(
        buyer_id=buyer.id,
        name=data.name,
        reference_id=data.reference_id,
        description=data.description,
        pickup_location=data.pickup_location,
        destination_location=data.destination_location,
        service_date=data.service_date,
        bid_start_time=data.bid_start_time,
        bid_close_time=data.bid_close_time,
        current_close_time=data.bid_close_time,
        forced_close_time=data.forced_close_time,
        status=RFQStatus.UPCOMING,
    )
    db.add(rfq)
    db.flush()
    cfg = data.auction_config
    db.add(AuctionConfig(
        rfq_id=rfq.id,
        trigger_window_minutes=cfg.trigger_window_minutes,
        extension_duration_minutes=cfg.extension_duration_minutes,
        trigger_type=cfg.trigger_type,
    ))
    db.add(ActivityLog(
        rfq_id=rfq.id, event_type=ActivityEventType.RFQ_CREATED,
        actor_user_id=buyer.id,
        message=f"RFQ '{rfq.name}' ({rfq.reference_id}) created.",
    ))
    db.commit()
    db.refresh(rfq)
    return rfq


def list_rfqs(db: Session, viewer: User, status_filter, search, page, page_size):
    q = db.query(RFQ)
    if viewer.role == UserRole.BUYER:
        q = q.filter(RFQ.buyer_id == viewer.id)
    if search:
        like = f"%{search}%"
        q = q.filter((RFQ.name.ilike(like)) | (RFQ.reference_id.ilike(like)))

    rfqs = q.order_by(RFQ.created_at.desc()).all()
    # reconcile statuses for fresh reads
    now = datetime.now(timezone.utc)
    for r in rfqs:
        if r.status in (RFQStatus.UPCOMING, RFQStatus.ACTIVE):
            reconcile_rfq_status(db, r, now)
    db.commit()

    if status_filter:
        rfqs = [r for r in rfqs if r.status == status_filter]
    total = len(rfqs)
    start = (page - 1) * page_size
    items = [_enrich(db, r, viewer) for r in rfqs[start:start + page_size]]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_rfq_or_404(db: Session, rfq_id: int, viewer: User) -> RFQ:
    rfq = db.get(RFQ, rfq_id)
    if rfq is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "RFQ not found")
    if viewer.role == UserRole.BUYER and rfq.buyer_id != viewer.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your RFQ")
    reconcile_rfq_status(db, rfq)
    db.commit()
    return rfq


def update_rfq(db: Session, rfq: RFQ, data: RFQUpdate) -> RFQ:
    if rfq.status != RFQStatus.UPCOMING:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Only upcoming RFQs can be edited")
    fields = data.model_dump(exclude_unset=True, exclude={"auction_config"})
    for k, v in fields.items():
        setattr(rfq, k, v)
    if data.bid_close_time and not data.auction_config:
        rfq.current_close_time = data.bid_close_time
    # revalidate timing
    if rfq.bid_start_time >= rfq.bid_close_time:
        raise HTTPException(400, "bid_start_time must be before bid_close_time")
    if rfq.forced_close_time <= rfq.bid_close_time:
        raise HTTPException(400, "forced_close_time must be later than bid_close_time")
    if "bid_close_time" in fields:
        rfq.current_close_time = rfq.bid_close_time
    if data.auction_config:
        cfg = rfq.auction_config
        cfg.trigger_window_minutes = data.auction_config.trigger_window_minutes
        cfg.extension_duration_minutes = data.auction_config.extension_duration_minutes
        cfg.trigger_type = data.auction_config.trigger_type
    db.add(ActivityLog(
        rfq_id=rfq.id, event_type=ActivityEventType.RFQ_UPDATED,
        message=f"RFQ '{rfq.name}' updated.",
    ))
    db.commit()
    db.refresh(rfq)
    return rfq


def delete_rfq(db: Session, rfq: RFQ):
    if rfq.status != RFQStatus.UPCOMING:
        raise HTTPException(400, "Only upcoming RFQs can be deleted")
    db.delete(rfq)
    db.commit()


def dashboard_stats(db: Session, viewer: User) -> dict:
    now = datetime.now(timezone.utc)
    q = db.query(RFQ)
    if viewer.role == UserRole.BUYER:
        q = q.filter(RFQ.buyer_id == viewer.id)
    rfqs = q.all()
    counts = {s: 0 for s in RFQStatus}
    for r in rfqs:
        st = reconcile_rfq_status(db, r, now)
        counts[st] += 1
    db.commit()

    if viewer.role == UserRole.BUYER:
        total_bids = db.query(func.count(Bid.id)).join(RFQ, Bid.rfq_id == RFQ.id).filter(
            RFQ.buyer_id == viewer.id
        ).scalar() or 0
        total_suppliers = db.query(func.count(Supplier.id)).scalar() or 0
        total_rfqs = len(rfqs)
    else:
        sid = viewer.supplier_profile.id if viewer.supplier_profile else -1
        total_bids = db.query(func.count(Bid.id)).filter(Bid.supplier_id == sid).scalar() or 0
        total_suppliers = db.query(func.count(SupplierQuote.id)).filter(
            SupplierQuote.supplier_id == sid
        ).scalar() or 0
        total_rfqs = len(rfqs)

    return {
        "total_rfqs": total_rfqs,
        "active_auctions": counts[RFQStatus.ACTIVE],
        "upcoming_auctions": counts[RFQStatus.UPCOMING],
        "closed_auctions": counts[RFQStatus.CLOSED] + counts[RFQStatus.FORCE_CLOSED],
        "total_suppliers": total_suppliers,
        "total_bids": total_bids,
    }
