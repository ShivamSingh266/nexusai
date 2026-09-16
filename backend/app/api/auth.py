from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import Role, User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

PUBLIC_REGISTRATION_ROLES = frozenset({"applicant", "recruiter"})


def build_auth_response(user: User) -> AuthResponse:
    role_name = user.role.name

    return AuthResponse(
        data=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=role_name,
            is_active=user.is_active,
        ),
        meta={},
        model_version=None,
        source_version="backend-v1",
        generated_at=datetime.now(timezone.utc).isoformat(),
        warnings=[],
        access_token=create_access_token(user.id, role_name),
        refresh_token=create_refresh_token(user.id),
        token_type="bearer",
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    if request.role not in PUBLIC_REGISTRATION_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This role cannot be self-registered.",
        )

    existing_user = db.scalar(
        select(User).where(User.email == request.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    role = db.scalar(
        select(Role).where(Role.name == request.role)
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role",
        )

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role_id=role.id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return build_auth_response(user)


@router.post(
    "/login",
    response_model=AuthResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(User.email == request.email)
    )

    if user is None or not verify_password(
        request.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return build_auth_response(user)
