"""
Suppliers Module — SQLAlchemy Models
Table: suppliers

Derived from the 15-record SUPPLIERS list in the prototype.
"""

import uuid

from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, func

from backend.base_model import Base, TimestampMixin


class Supplier(TimestampMixin, Base):
    """Supplier / vendor master record.

    Synced from the external Vendor Management Portal via Kafka events.
    """

    __tablename__ = "suppliers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    code = Column(String(20), unique=True, nullable=False, index=True)
    legal_name = Column(String(500), nullable=False)
    gstin = Column(String(15), unique=True, nullable=False, index=True)
    pan = Column(String(10), nullable=True)
    state = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    is_msme = Column(Boolean, nullable=False, default=False)
    msme_category = Column(String(10), nullable=True)  # MICRO / SMALL / MEDIUM
    bank_account = Column(String(50), nullable=True)
    bank_name = Column(String(100), nullable=True)
    ifsc = Column(String(11), nullable=True)
    payment_terms = Column(Integer, nullable=True, default=30)  # days
    risk_score = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE / SUSPENDED / BLOCKED
    vendor_portal_status = Column(String(30), nullable=True)
    contact_email = Column(String(255), nullable=True)
    onboarded_date = Column(String(20), nullable=True)  # stored as date string for SQLite compat
    last_synced_from_portal = Column(DateTime, nullable=True)
