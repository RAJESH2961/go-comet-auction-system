"""Bid submission validation for the British auction engine."""
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from ..models.rfq import RFQ, RFQStatus
from ..models.supplier import Supplier
from ..models.supplier_quote import SupplierQuote


class BidValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_bid_submission(
    db: Session,
    rfq: RFQ,
    supplier: Supplier,
    amount: Decimal,
    now: datetime,
) -> SupplierQuote:
    """Validate a new bid. Returns the supplier's quote on success,
    raises BidValidationError otherwise."""
    if amount is None or amount <= 0:
        raise BidValidationError("Bid amount must be a positive number")

    quote = (
        db.query(SupplierQuote)
        .filter(
            SupplierQuote.rfq_id == rfq.id,
            SupplierQuote.supplier_id == supplier.id,
        )
        .first()
    )
    if quote is None:
        raise BidValidationError(
            "You must submit an initial quotation before bidding in this auction",
            status_code=403,
        )

    if now < rfq.bid_start_time:
        raise BidValidationError("Auction has not started yet")
    if rfq.status in (RFQStatus.CLOSED, RFQStatus.FORCE_CLOSED):
        raise BidValidationError("Auction is closed")
    if now >= rfq.forced_close_time:
        raise BidValidationError("Auction has reached its forced closing time")
    if now >= rfq.current_close_time:
        raise BidValidationError("Auction bidding window has closed")

    # Baseline = supplier's latest valid bid, else their initial quote total
    from ..models.bid import Bid

    last = (
        db.query(Bid)
        .filter(Bid.rfq_id == rfq.id, Bid.supplier_id == supplier.id)
        .order_by(Bid.created_at.desc(), Bid.id.desc())
        .first()
    )
    baseline = last.amount if last else quote.total_amount
    if amount >= baseline:
        raise BidValidationError(
            f"New bid must be lower than your current bid of {baseline}"
        )
    return quote
