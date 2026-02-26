"""
Notifications Module — FastAPI Routes

Prefix: ``/api/notifications``

User notification management — list, read, mark-as-read.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.dependencies import get_db, get_current_user
from backend.modules.notifications.schemas import (
    NotificationResponse,
    NotificationCreate,
    UnreadCountResponse,
)
from backend.modules.notifications import service

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# ---------------------------------------------------------------------------
# GET  /api/notifications
# ---------------------------------------------------------------------------

@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
) -> List[NotificationResponse]:
    """List notifications for the current user (all in dev mode)."""
    user_id = user.get("sub")
    if user_id == "dev-user":
        user_id = None  # show all notifications in dev mode
    items = await service.list_notifications(
        db,
        user_id=user_id,
        unread_only=unread_only,
        limit=limit,
    )
    return [NotificationResponse.model_validate(i) for i in items]


# ---------------------------------------------------------------------------
# GET  /api/notifications/unread-count
# ---------------------------------------------------------------------------

@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
) -> UnreadCountResponse:
    """Return count of unread notifications."""
    user_id = user.get("sub")
    if user_id == "dev-user":
        user_id = None
    count = await service.get_unread_count(db, user_id=user_id)
    return UnreadCountResponse(count=count)


# ---------------------------------------------------------------------------
# POST  /api/notifications (admin / system use)
# ---------------------------------------------------------------------------

@router.post("", response_model=NotificationResponse, status_code=201)
async def create_notification(
    body: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> NotificationResponse:
    """Create a notification (admin/system use)."""
    result = await service.create_notification(
        db,
        notification_type=body.notification_type,
        title=body.title,
        severity=body.severity,
        message=body.message,
        link=body.link,
        user_id=body.user_id,
    )
    return NotificationResponse.model_validate(result)


# ---------------------------------------------------------------------------
# PATCH  /api/notifications/{notif_id}/read
# ---------------------------------------------------------------------------

@router.patch("/{notif_id}/read", response_model=NotificationResponse)
async def mark_read(
    notif_id: str,
    db: AsyncSession = Depends(get_db),
    _user: Dict[str, Any] = Depends(get_current_user),
) -> NotificationResponse:
    """Mark a single notification as read."""
    result = await service.mark_read(db, notif_id)
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found")
    return NotificationResponse.model_validate(result)


# ---------------------------------------------------------------------------
# POST  /api/notifications/mark-all-read
# ---------------------------------------------------------------------------

@router.post("/mark-all-read")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Mark all notifications as read for the current user."""
    count = await service.mark_all_read(db, user_id=user.get("sub"))
    return {"marked_read": count}
