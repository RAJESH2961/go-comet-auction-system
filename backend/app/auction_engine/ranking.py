"""Supplier ranking logic for the British auction.

Rankings are derived from each participating supplier's latest valid bid.
The lowest bid gets L1. Ties are broken deterministically by the earliest
submission time, then by supplier id.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.bid import Bid
from ..models.supplier import Supplier
from ..models.supplier_quote import SupplierQuote


@dataclass
class RankedBid:
    rank: int
    supplier_id: int
    supplier_name: str
    company_name: str | None
    amount: Decimal
    bid_time: datetime
    transit_time: str | None

    @property
    def rank_label(self) -> str:
        return f"L{self.rank}"


def latest_bid_per_supplier(db: Session, rfq_id: int) -> dict[int, Bid]:
    """Return {supplier_id: latest Bid}. Falls back to the supplier's initial
    quotation total when they have not placed a competitive bid yet, so that
    quoting suppliers appear in the ranking."""
    bids = (
        db.query(Bid)
        .filter(Bid.rfq_id == rfq_id)
        .order_by(Bid.supplier_id, Bid.created_at.desc(), Bid.id.desc())
        .all()
    )
    latest: dict[int, Bid] = {}
    for b in bids:
        if b.supplier_id not in latest:
            latest[b.supplier_id] = b
    return latest


def compute_rankings(db: Session, rfq_id: int) -> list[RankedBid]:
    """Compute current supplier rankings for an RFQ.

    Baseline amount = latest competitive bid, or the initial quotation total
    when no bid has been placed yet.
    """
    latest = latest_bid_per_supplier(db, rfq_id)
    quotes = db.query(SupplierQuote).filter(SupplierQuote.rfq_id == rfq_id).all()
    supplier_ids = set(latest) | {q.supplier_id for q in quotes}
    if not supplier_ids:
        return []
    suppliers = {
        s.id: s for s in db.query(Supplier).filter(Supplier.id.in_(supplier_ids)).all()
    }
    quotes_by_supplier = {q.supplier_id: q for q in quotes}

    entries = []
    for sid in supplier_ids:
        bid = latest.get(sid)
        quote = quotes_by_supplier.get(sid)
        if bid is not None:
            amount, bid_time = bid.amount, bid.created_at
        elif quote is not None:
            amount, bid_time = quote.total_amount, quote.created_at
        else:
            continue
        sup = suppliers.get(sid)
        name = (
            (sup.user.full_name if sup and sup.user else None)
            or (sup.company_name if sup else None)
            or f"Supplier {sid}"
        )
        entries.append(
            RankedBid(
                rank=0,
                supplier_id=sid,
                supplier_name=name,
                company_name=sup.company_name if sup else None,
                amount=amount,
                bid_time=bid_time,
                transit_time=quote.transit_time if quote else None,
            )
        )

    # Lowest amount first; tie-break: earliest submission, then supplier id
    entries.sort(key=lambda e: (e.amount, e.bid_time, e.supplier_id))
    rank = 0
    prev_key = None
    for i, e in enumerate(entries):
        key = e.amount
        if prev_key is None or key != prev_key:
            rank = i + 1
        e.rank = rank
        prev_key = key
    return entries


def rank_map(rankings: list[RankedBid]) -> dict[int, int]:
    return {r.supplier_id: r.rank for r in rankings}
