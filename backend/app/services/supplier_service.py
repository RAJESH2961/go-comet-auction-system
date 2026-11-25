from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.bid import Bid
from ..models.supplier import Supplier
from ..models.supplier_quote import SupplierQuote


def list_suppliers(db: Session) -> list[dict]:
    suppliers = db.query(Supplier).all()
    out = []
    for s in suppliers:
        out.append({
            "id": s.id,
            "user_id": s.user_id,
            "full_name": s.user.full_name if s.user else s.contact_name or "",
            "email": s.user.email if s.user else "",
            "company_name": s.company_name,
            "phone": s.phone,
            "created_at": s.created_at,
            "quotes_count": db.query(func.count(SupplierQuote.id)).filter(
                SupplierQuote.supplier_id == s.id).scalar() or 0,
            "bids_count": db.query(func.count(Bid.id)).filter(
                Bid.supplier_id == s.id).scalar() or 0,
        })
    return out


def get_supplier_or_404(db: Session, supplier_id: int) -> dict:
    s = db.get(Supplier, supplier_id)
    if s is None:
        raise HTTPException(404, "Supplier not found")
    return {
        "id": s.id, "user_id": s.user_id,
        "full_name": s.user.full_name if s.user else "",
        "email": s.user.email if s.user else "",
        "company_name": s.company_name, "phone": s.phone,
        "created_at": s.created_at,
        "quotes_count": db.query(func.count(SupplierQuote.id)).filter(
            SupplierQuote.supplier_id == s.id).scalar() or 0,
        "bids_count": db.query(func.count(Bid.id)).filter(
            Bid.supplier_id == s.id).scalar() or 0,
    }
