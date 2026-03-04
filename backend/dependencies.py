from __future__ import annotations

from typing import Dict, Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database import get_db as _get_db
from backend.modules.auth.constants import ROLE_HIERARCHY

# ---------------------------------------------------------------------------
# Database dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Yield an async database session (delegates to backend.database.get_db)."""
    async for session in _get_db():
        yield session


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> Dict[str, Any]:
    """Extract and validate the current user from the JWT in the Authorization header.

    If ``settings.AUTH_ENABLED`` is False the dependency returns a default
    dev-mode user dict so that endpoints work without a real token.
    """
    if not settings.AUTH_ENABLED:
        return {
            "sub": "dev-user",
            "name": "Developer",
            "role": "admin",
        }

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


# ---------------------------------------------------------------------------
# Role-based access control dependency
# ---------------------------------------------------------------------------


def require_role(min_role: str):
    """Dependency factory: returns a dependency that enforces a minimum role.

    Usage:
        @router.post("/", dependencies=[Depends(require_role("PROCUREMENT_MANAGER"))])
        async def create_something(...): ...

    Or to also receive the user dict:
        async def endpoint(user=Depends(require_role("FINANCE_HEAD"))): ...
    """
    required_level = ROLE_HIERARCHY.get(min_role, 0)

    async def _check_role(
        current_user: Dict[str, Any] = Depends(get_current_user),
    ) -> Dict[str, Any]:
        user_role = (current_user.get("role") or "").upper()
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        if user_level < required_level:
            from backend.exceptions import AuthorizationError
            raise AuthorizationError(
                f"Role {min_role} or higher required. Your role: {user_role}"
            )
        return current_user

    return _check_role


# ---------------------------------------------------------------------------
# Pagination helper
# ---------------------------------------------------------------------------


def paginate(items: list, skip: int = 0, limit: int = 50) -> Dict[str, Any]:
    """Apply pagination to a list and return a standardized response.

    Returns:
        {"items": [...], "total": N, "skip": skip, "limit": limit}
    """
    total = len(items)
    sliced = items[skip : skip + limit]
    return {"items": sliced, "total": total, "skip": skip, "limit": limit}
