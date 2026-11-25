"""Shared event payload builders for auction broadcasts."""
from ..auction_engine.ranking import RankedBid


def rankings_payload(rankings: list[RankedBid], viewer_supplier_id: int | None = None):
    return [
        {
            "rank": r.rank,
            "rank_label": r.rank_label,
            "supplier_id": r.supplier_id,
            "supplier_name": r.supplier_name,
            "company_name": r.company_name,
            "latest_bid": r.amount,
            "transit_time": r.transit_time,
            "bid_time": r.bid_time,
            "is_me": viewer_supplier_id is not None and r.supplier_id == viewer_supplier_id,
        }
        for r in rankings
    ]
