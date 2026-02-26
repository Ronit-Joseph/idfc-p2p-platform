"""
Notifications Module — Pydantic Schemas
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    notification_type: str
    severity: str
    title: str
    message: Optional[str] = None
    link: Optional[str] = None
    is_read: bool
    created_at: Optional[str] = None


class NotificationCreate(BaseModel):
    user_id: Optional[str] = None
    notification_type: str
    severity: str = "INFO"
    title: str
    message: Optional[str] = None
    link: Optional[str] = None


class UnreadCountResponse(BaseModel):
    count: int
