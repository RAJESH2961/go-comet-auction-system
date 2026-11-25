from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.activity_log import ActivityLog, ActivityEventType
from ..models.rfq import RFQ, RFQStatus
from ..models.supplier import Supplier
from ..models.supplier_quote import SupplierQuote
from ..models.user import User, UserRole
from ..schemas.quote import QuoteCreate, QuoteOut
from ..services import rfq_service
from ..utils.dependencies import get_current_user, require_supplier
from ..websocket.events import rankings_payload
from ..websocket.manager import broadcast_threadsafe
from ..auction_engine.ranking import compute_rankings

router = APIRouter(prefix="/api/rfqs/{rfq_id}/quotes", tags=["quotes"])


def _out(q: SupplierQuote) -> dict:
    return {
        "id": q.id, "rfq_id": q.rfq_id, "supplier_id": q.supplier_id,
        "supplier_name": (
            q.supplier.company_name or q.supplier.user.full_name
            if q.supplier else None
        ),
        "carrier_name": q.carrier_name,
        "freight_charges": q.freight_charges,
        "origin_charges": q.origin_charges,
        "destination_charges": q.destination_charges,
        "total_amount": q.total_amount,
        "transit_time": q.transit_time,
        "validity_of_quote": q.validity_of_quote,
        "created_at": q.created_at,
    }


@router.post("", response_model=QuoteOut, status_code=201)
def submit_quote(
    rfq_id: int,
    data: QuoteCreate,
    supplier: Supplier = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    rfq = db.get(RFQ, rfq_id)
    if rfq is None:
        raise HTTPException(404, "RFQ not found")
    rfq_service.reconcile_rfq_status(db, rfq)
    db.commit()
    if rfq.status in (RFQStatus.CLOSED, RFQStatus.FORCE_CLOSED):
        raise HTTPException(400, "Auction is closed")

    existing = db.query(SupplierQuote).filter(
        SupplierQuote.rfq_id == rfq_id,
        SupplierQuote.supplier_id == supplier.id,
    ).first()
    if existing:
        raise HTTPException(409, "You have already submitted a quotation for this RFQ")

    total = data.freight_charges + data.origin_charges + data.destination_charges
    quote = SupplierQuote(
        rfq_id=rfq_id, supplier_id=supplier.id,
        carrier_name=data.carrier_name,
        freight_charges=data.freight_charges,
        origin_charges=data.origin_charges,
        destination_charges=data.destination_charges,
        total_amount=total,
        transit_time=data.transit_time,
        validity_of_quote=data.validity_of_quote,
    )
    db.add(quote)
    db.add(ActivityLog(
        rfq_id=rfq_id, event_type=ActivityEventType.SUPPLIER_JOINED,
        actor_user_id=supplier.user_id, supplier_id=supplier.id,
        message=f"{supplier.company_name or 'A supplier'} joined the auction.",
    ))
    db.add(ActivityLog(
        rfq_id=rfq_id, event_type=ActivityEventType.QUOTE_SUBMITTED,
        actor_user_id=supplier.user_id, supplier_id=supplier.id,
        message=f"Initial quotation of {total} submitted.",
        event_metadata={"total_amount": str(total), "carrier": data.carrier_name},
    ))
    db.commit()
    db.refresh(quote)

    broadcast_threadsafe(rfq_id, "rankings", {
        "rankings": rankings_payload(compute_rankings(db, rfq_id)),
    })
    return _out(quote)


@router.get("", response_model=list[QuoteOut])
def list_quotes(
    rfq_id: int,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rfq = db.get(RFQ, rfq_id)
    if rfq is None:
        raise HTTPException(404, "RFQ not found")
    q = db.query(SupplierQuote).filter(SupplierQuote.rfq_id == rfq_id)
    if viewer.role == UserRole.BUYER:
        if rfq.buyer_id != viewer.id:
            raise HTTPException(403, "Not your RFQ")
    else:
        # suppliers only see their own private quotation details
        sid = viewer.supplier_profile.id if viewer.supplier_profile else -1
        q = q.filter(SupplierQuote.supplier_id == sid)
    return [_out(x) for x in q.order_by(SupplierQuote.created_at).all()]
