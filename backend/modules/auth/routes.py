"""
Auth Module — API Routes

Endpoints: register, login, me, list-users.
"""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.dependencies import get_db, get_current_user
from backend.exceptions import AuthenticationError, AuthorizationError
from backend.modules.auth.constants import ADMIN
from backend.modules.auth.models import User
from backend.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    UserCreate,
    UserResponse,
)
from backend.modules.auth.service import (
    authenticate_user,
    create_access_token,
    create_user,
    get_all_users,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user account."""
    user = await create_user(db, data)
    return user


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password and receive a JWT."""
    user = await authenticate_user(db, data.email, data.password)
    if user is None:
        raise AuthenticationError("Invalid email or password")

    token = create_access_token(
        {
            "sub": user.id,
            "role": user.role,
            "name": user.full_name,
        }
    )
    return LoginResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserResponse)
async def me(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the profile of the currently authenticated user.

    When AUTH_ENABLED is False, the dependency returns a dev-user stub.
    If a real Bearer token is provided, decode it to find the actual user.
    """
    user_id = current_user.get("sub")

    # If auth is disabled but a real token was sent, decode it
    if user_id == "dev-user":
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            from jose import jwt, JWTError
            try:
                payload = jwt.decode(
                    auth_header[7:],
                    settings.JWT_SECRET,
                    algorithms=[settings.JWT_ALGORITHM],
                )
                user_id = payload.get("sub")
            except JWTError:
                pass

    if user_id is None or user_id == "dev-user":
        raise AuthenticationError("Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise AuthenticationError("User not found")

    return user


# ---------------------------------------------------------------------------
# GET /api/auth/users  (admin only)
# ---------------------------------------------------------------------------


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users. Restricted to ADMIN role."""
    role = current_user.get("role", "")
    if role.upper() != ADMIN:
        raise AuthorizationError("Only admins can list users")

    users = await get_all_users(db)
    return users
