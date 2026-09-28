from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):

    existing_user = db.scalar(
        select(User).where(
            User.email == request.email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered.",
        )

    user = User(
        email=request.email,
        password_hash=hash_password(
            request.password
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        str(user.id)
    )

    return TokenResponse(
        access_token=token
    )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):

    user = db.scalar(
        select(User).where(
            User.email == request.email
        )
    )

    if (
        user is None
        or not verify_password(
            request.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        str(user.id)
    )

    return TokenResponse(
        access_token=token
    )