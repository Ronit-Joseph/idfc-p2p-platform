"""
Auth Module — SQLAlchemy Models
Table: users
"""

import uuid

from sqlalchemy import Column, String, Boolean, DateTime, func

from backend.base_model import Base, TimestampMixin


class User(TimestampMixin, Base):
    """Platform user account.

    Roles: ADMIN, FINANCE_HEAD, PROCUREMENT_MANAGER, DEPARTMENT_HEAD, VIEWER
    """

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    department = Column(String(50), nullable=True)
    role = Column(String(50), nullable=False, default="VIEWER")
    is_active = Column(Boolean, nullable=False, default=True)
