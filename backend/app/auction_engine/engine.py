"""Auction engine orchestration — the transactional heart of bidding.

place_bid() runs inside a single PostgreSQL transaction:
  1. SELECT ... FOR UPDATE on the RFQ row (serializes concurrent bids).
  2. Validate the bid.
  3. Snapshot rankings BEFORE the bid.
  4. Insert the bid (immutable history).
  5. Recompute rankings AFTER the bid.
  6. Evaluate the configured extension trigger and update close time.
  7. Log all activity.
The caller commits, then broadcasts WebSocket events.
"""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from ..models.activity_log import ActivityLog, ActivityEventType
from ..models.bid import Bid
from ..models.rfq import RFQ, RFQStatus
from ..models.supplier import Supplier
from .extension import ExtensionResult, evaluate_extension
from .ranking import RankedBid, compute_rankings, rank_map
from .validation import BidValidationError, utcnow, validate_bid_submission


@dataclass
class BidResult:
    bid: Bid
    rankings_after: list[RankedBid]
    extension: ExtensionResult
    rank_changes: dict = field(default_factory=dict)
    lowest_bid: Decimal | None = None
    l1_supplier_id: int | None = None


def place_bid(
    db: Session,
    rfq_id: int,
    supplier: Supplier,
    amount: Decimal,
    now: datetime | None = None,
) -> BidResult:
    """Process a bid atomically. Caller must commit the session."""
    now = now or utcnow()

    # Row-level lock serializes concurrent bid submissions on this RFQ
    rfq = (
        db.query(RFQ)
        .filter(RFQ.id == rfq_id)
        .with_for_update()
        .first()
    )
    if rfq is None:
        raise BidValidationError("RFQ not found", status_code=404)

    # Reconcile overdue status before accepting anything
    if rfq.status in (RFQStatus.UPCOMING, RFQStatus.ACTIVE):
        from .closing import reconcile_rfq_status
        reconcile_rfq_status(db, rfq, now)

    validate_bid_submission(db, rfq, supplier, amount, now)

    rankings_before = compute_rankings(db, rfq.id)
    prev_bid = (
        db.query(Bid)
        .filter(Bid.rfq_id == rfq.id, Bid.supplier_id == supplier.id)
        .order_by(Bid.created_at.desc(), Bid.id.desc())
        .first()
    )

    bid = Bid(rfq_id=rfq.id, supplier_id=supplier.id, amount=amount, created_at=now)
    db.add(bid)
    db.flush()

    rankings_after = compute_rankings(db, rfq.id)

    db.add(ActivityLog(
        rfq_id=rfq.id,
        event_type=ActivityEventType.BID_RECEIVED,
        actor_user_id=supplier.user_id,
        supplier_id=supplier.id,
        message=f"Bid of {amount} submitted.",
        event_metadata={
            "bid_id": bid.id,
            "amount": str(amount),
            "previous_amount": str(prev_bid.amount) if prev_bid else None,
        },
    ))

    before_map, after_map = rank_map(rankings_before), rank_map(rankings_after)
    changed = {
        sid: {"from": before_map.get(sid), "to": r}
        for sid, r in after_map.items()
        if before_map.get(sid) != r
    }
    if changed:
        db.add(ActivityLog(
            rfq_id=rfq.id,
            event_type=ActivityEventType.RANK_CHANGED,
            supplier_id=supplier.id,
            message="Supplier rankings updated.",
            event_metadata={"changes": {str(k): v for k, v in changed.items()}},
        ))

    extension = evaluate_extension(rfq, rankings_before, rankings_after, now)
    if extension.extended:
        rfq.current_close_time = extension.new_close_time
        db.add(ActivityLog(
            rfq_id=rfq.id,
            event_type=ActivityEventType.AUCTION_EXTENDED,
            supplier_id=supplier.id,
            message=f"Auction extended: {extension.reason}",
            event_metadata={
                "reason": extension.reason,
                "previous_close_time": extension.previous_close_time.isoformat(),
                "new_close_time": extension.new_close_time.isoformat(),
            },
        ))

    return BidResult(
        bid=bid,
        rankings_after=rankings_after,
        extension=extension,
        rank_changes=changed,
        lowest_bid=rankings_after[0].amount if rankings_after else None,
        l1_supplier_id=rankings_after[0].supplier_id if rankings_after else None,
    )
