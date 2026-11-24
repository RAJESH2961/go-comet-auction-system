from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.supplier import Supplier
from ..models.user import User, UserRole
from ..schemas.auth import RegisterRequest
from ..utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


def register_user(db: Session, data: RegisterRequest) -> User:
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email is already registered")
    user = User(
        full_name=data.full_name,
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        role=data.role,
        company_name=data.company_name,
        phone=data.phone,
    )
    db.add(user)
    db.flush()
    if data.role == UserRole.SUPPLIER:
        db.add(Supplier(
            user_id=user.id,
            company_name=data.company_name,
            contact_name=data.full_name,
            phone=data.phone,
        ))
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email.lower()).first()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled")
    return user


def issue_tokens(user: User) -> dict:
    return {
        "access_token": create_access_token(user.id, user.role.value),
        "refresh_token": create_refresh_token(user.id),
    }
