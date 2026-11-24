from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.supplier import Supplier
from ..models.user import User, UserRole
from .security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    try:
        payload = decode_token(creds.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def require_buyer(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.BUYER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Buyer role required")
    return user


def require_supplier(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Supplier:
    if user.role != UserRole.SUPPLIER:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Supplier role required")
    supplier = db.query(Supplier).filter(Supplier.user_id == user.id).first()
    if supplier is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Supplier profile not found")
    return supplier
