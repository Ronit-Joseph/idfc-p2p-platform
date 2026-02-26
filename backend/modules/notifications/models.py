"""
Notifications Module — SQLAlchemy Models
Table: notifications

Platform notifications for users — MSME alerts, EBS failures,
approval requests, fraud warnings, etc.
"""

import uuid

from sqlalchemy import Column, String, Boolean, Text, DateTime, func

from backend.base_model import Base


class Notification(Base):
    """User notification.

    notification_type: MSME_ALERT, EBS_FAILURE, APPROVAL_REQUEST,
                       FRAUD_WARNING, GST_ISSUE, VENDOR_EVENT, etc.
    severity: INFO, WARNING, CRITICAL.
    """

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    user_id = Column(String(36), nullable=True, index=True)  # FK conceptual to users
    notification_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False, default="INFO")  # INFO / WARNING / CRITICAL
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    link = Column(String(255), nullable=True)  # Frontend route to navigate to
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
