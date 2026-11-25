"""Auction status computation and forced/normal closing logic."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..models.activity_log import ActivityLog, ActivityEventType
from ..models.rfq import RFQ, RFQStatus


def utcnow():
    return datetime.now(timezone.utc)


def compute_status(rfq: RFQ, now: datetime) -> RFQStatus:
    if now < rfq.bid_start_time:
        return RFQStatus.UPCOMING
    if now >= rfq.forced_close_time or (
        rfq.current_close_time >= rfq.forced_close_time and now >= rfq.current_close_time
    ):
        return RFQStatus.FORCE_CLOSED
    if now >= rfq.current_close_time:
        return RFQStatus.CLOSED
    return RFQStatus.ACTIVE


def reconcile_rfq_status(db: Session, rfq: RFQ, now: datetime | None = None) -> RFQStatus:
    """Recompute and persist status; log closing events. Caller commits."""
    now = now or utcnow()
    new_status = compute_status(rfq, now)
    if new_status != rfq.status:
        if new_status == RFQStatus.ACTIVE:
            db.add(ActivityLog(
                rfq_id=rfq.id, event_type=ActivityEventType.AUCTION_STARTED,
                message=f"Auction '{rfq.name}' started.",
            ))
        elif new_status == RFQStatus.CLOSED:
            db.add(ActivityLog(
                rfq_id=rfq.id, event_type=ActivityEventType.AUCTION_CLOSED,
                message=f"Auction '{rfq.name}' closed at scheduled close time.",
                event_metadata={"closed_at": now.isoformat()},
            ))
        elif new_status == RFQStatus.FORCE_CLOSED:
            db.add(ActivityLog(
                rfq_id=rfq.id, event_type=ActivityEventType.AUCTION_FORCE_CLOSED,
                message=f"Auction '{rfq.name}' reached forced closing time.",
                event_metadata={"forced_close_time": rfq.forced_close_time.isoformat()},
            ))
        rfq.status = new_status
    return rfq.status


def close_due_auctions(db: Session, now: datetime | None = None) -> list[RFQ]:
    """Close auctions whose time has passed and start upcoming ones.

    Returns RFQs whose status changed (for WebSocket broadcast)."""
    now = now or utcnow()
    candidates = (
        db.query(RFQ)
        .filter(
            RFQ.status.in_([RFQStatus.UPCOMING, RFQStatus.ACTIVE]),
            RFQ.bid_start_time <= now,
        )
        .all()
    )
    changed = []
    for rfq in candidates:
        old = rfq.status
        if reconcile_rfq_status(db, rfq, now) != old:
            changed.append(rfq)
    db.commit()
    return changed
