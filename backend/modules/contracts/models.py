"""
Contracts Module — SQLAlchemy Models
Table: contracts

Contract Lifecycle Management (CLM) for vendor agreements.
Covers MSA, SOW, NDA, SLA, and amendment tracking.
"""

import uuid

from sqlalchemy import Column, String, Float, Boolean, Integer, Text, DateTime, func

from backend.base_model import Base, TimestampMixin


class Contract(TimestampMixin, Base):
    """Vendor contract.

    Lifecycle: DRAFT -> ACTIVE -> EXPIRED / TERMINATED / RENEWED
    """

    __tablename__ = "contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    contract_number = Column(String(30), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    supplier_id = Column(String(36), nullable=True, index=True)
    supplier_name = Column(String(255), nullable=True)
    contract_type = Column(String(20), nullable=False)  # MSA / SOW / NDA / SLA / AMENDMENT
    status = Column(String(20), nullable=False, default="DRAFT")  # DRAFT / ACTIVE / EXPIRED / TERMINATED / RENEWED
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    value = Column(Float, nullable=True, default=0)
    currency = Column(String(5), nullable=False, default="INR")
    auto_renew = Column(Boolean, nullable=False, default=False)
    renewal_notice_days = Column(Integer, nullable=True, default=30)
    department = Column(String(50), nullable=True)
    owner = Column(String(255), nullable=True)
    terms_summary = Column(Text, nullable=True)
