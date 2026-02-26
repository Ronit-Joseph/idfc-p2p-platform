"""
Auth Module — Pydantic Schemas

Request / response models for authentication endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from backend.modules.auth.constants import ALL_ROLES, VIEWER


class UserCreate(BaseModel):
    """Payload for user registration."""

    email: str
    password: str = Field(..., min_length=8, description="Plain-text password (min 8 chars)")
    full_name: str = Field(..., min_length=1, max_length=255)
    department: Optional[str] = Field(None, max_length=50)
    role: str = Field(default=VIEWER, description="One of: " + ", ".join(ALL_ROLES))


class UserResponse(BaseModel):
    """Public representation of a user (no password)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    department: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime


class LoginRequest(BaseModel):
    """Payload for login."""

    email: str
    password: str


class LoginResponse(BaseModel):
    """JWT token + user info returned on successful login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str
    role: str
    name: str
    exp: int
