"""Service layer bridging HTTP routes and the auction engine."""
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..auction_engine.engine import BidResult, BidValidationError, place_bid
from ..auction_engine.ranking import compute_rankings
from ..models.bid import Bid
from ..models.rfq import RFQ
from ..models.supplier import Supplier


def submit_bid(db: Session, rfq_id: int, supplier: Supplier, amount: Decimal) -> BidResult:
    """Validate + persist a bid inside one transaction, then commit.

    WebSocket broadcasts happen AFTER commit (caller responsibility)."""
    try:
        result = place_bid(db, rfq_id, supplier, amount)
        db.commit()
        return result
    except BidValidationError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(500, "Failed to process bid")


def get_bid_history(db: Session, rfq_id: int) -> list[dict]:
    bids = (
        db.query(Bid)
        .filter(Bid.rfq_id == rfq_id)
        .order_by(Bid.created_at.asc(), Bid.id.asc())
        .all()
    )
    prev_per_supplier: dict[int, Decimal] = {}
    out = []
    for b in bids:
        out.append({
            "id": b.id,
            "supplier_id": b.supplier_id,
            "supplier_name": (
                b.supplier.company_name or b.supplier.user.full_name
                if b.supplier else f"Supplier {b.supplier_id}"
            ),
            "amount": b.amount,
            "previous_amount": prev_per_supplier.get(b.supplier_id),
            "created_at": b.created_at,
        })
        prev_per_supplier[b.supplier_id] = b.amount
    return out
