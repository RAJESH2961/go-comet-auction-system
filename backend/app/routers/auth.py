import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.auth import (
    LoginRequest, ProfileUpdateRequest, RefreshRequest, RegisterRequest,
    TokenResponse, UserOut,
)
from ..services.auth_service import authenticate, issue_tokens, register_user
from ..utils.dependencies import get_current_user
from ..utils.security import decode_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_out(user: User) -> dict:
    return {
        "id": user.id, "full_name": user.full_name, "email": user.email,
        "role": user.role, "company_name": user.company_name, "phone": user.phone,
        "is_active": user.is_active, "created_at": user.created_at,
        "supplier_id": user.supplier_profile.id if user.supplier_profile else None,
    }


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    user = register_user(db, data)
    return {**issue_tokens(user), "user": _user_out(user)}


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, data.email, data.password)
    return {**issue_tokens(user), "user": _user_out(user)}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_out(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return {**issue_tokens(user), "user": _user_out(user)}


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    # Stateless JWT: client discards tokens. (For production, add a token
    # blocklist or rotate refresh tokens server-side.)
    return {"detail": "Logged out"}


@router.put("/profile", response_model=UserOut)
def update_profile(
    data: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    if user.supplier_profile:
        if data.company_name is not None:
            user.supplier_profile.company_name = data.company_name
        if data.phone is not None:
            user.supplier_profile.phone = data.phone
    db.commit()
    db.refresh(user)
    return _user_out(user)
