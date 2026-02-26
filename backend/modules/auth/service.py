"""
Auth Module — Service Layer

Business logic for user management and authentication.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.exceptions import ConflictError, AuthenticationError
from backend.modules.auth.models import User
from backend.modules.auth.schemas import UserCreate

# ---------------------------------------------------------------------------
# Password hashing (bcrypt via passlib)
# ---------------------------------------------------------------------------

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return _pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the bcrypt *hashed* value."""
    return _pwd_ctx.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT token creation
# ---------------------------------------------------------------------------


def create_access_token(data: dict) -> str:
    """Create a signed JWT with the given *data* payload.

    The token expires after ``settings.JWT_EXPIRY_MINUTES`` minutes.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


# ---------------------------------------------------------------------------
# User CRUD helpers
# ---------------------------------------------------------------------------


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user by email, or return None."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    """Register a new user.

    Raises ``ConflictError`` if the email is already taken.
    """
    existing = await get_user_by_email(db, data.email)
    if existing is not None:
        raise ConflictError(f"Email {data.email} is already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        department=data.department,
        role=data.role,
    )
    db.add(user)
    await db.flush()       # populate defaults (id, created_at) before returning
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Validate credentials and return the user, or None on failure."""
    user = await get_user_by_email(db, email)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


async def get_all_users(db: AsyncSession) -> list[User]:
    """Return every user in the database (admin-level listing)."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())
