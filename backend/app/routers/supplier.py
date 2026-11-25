from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.supplier import Supplier
from ..models.user import User
from ..schemas.auction import SupplierOut
from ..services import supplier_service
from ..utils.dependencies import get_current_user, require_buyer, require_supplier

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
def list_suppliers(
    buyer: User = Depends(require_buyer),
    db: Session = Depends(get_db),
):
    return supplier_service.list_suppliers(db)


@router.get("/me", response_model=SupplierOut)
def my_profile(
    supplier: Supplier = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    return supplier_service.get_supplier_or_404(db, supplier.id)


@router.get("/{supplier_id}", response_model=SupplierOut)
def get_supplier(
    supplier_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return supplier_service.get_supplier_or_404(db, supplier_id)
