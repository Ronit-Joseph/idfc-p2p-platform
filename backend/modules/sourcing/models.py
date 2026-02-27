"""
Sourcing Module — SQLAlchemy Models
Tables: rfq_events, rfq_responses

RFQ lifecycle management for structured vendor selection.
"""

import uuid

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, JSON, ForeignKey, func

from backend.base_model import Base, TimestampMixin


class RFQ(TimestampMixin, Base):
    """Request for Quotation.

    Lifecycle: DRAFT -> PUBLISHED -> EVALUATION -> AWARDED / CANCELLED
    """

    __tablename__ = "rfq_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    rfq_number = Column(String(30), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="DRAFT")
    category = Column(String(100), nullable=True)
    department = Column(String(50), nullable=True)
    budget_estimate = Column(Float, nullable=True, default=0)
    submission_deadline = Column(String(20), nullable=True)
    evaluation_criteria = Column(JSON, nullable=True)
    created_by = Column(String(255), nullable=True)


class RFQResponse(TimestampMixin, Base):
    """Supplier response/bid for an RFQ."""

    __tablename__ = "rfq_responses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), nullable=False)
    rfq_id = Column(String(36), ForeignKey("rfq_events.id"), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    quoted_amount = Column(Float, nullable=True, default=0)
    delivery_timeline = Column(String(100), nullable=True)
    technical_score = Column(Float, nullable=True)
    commercial_score = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="SUBMITTED")  # SUBMITTED / SHORTLISTED / AWARDED / REJECTED
    notes = Column(Text, nullable=True)
    submitted_at = Column(String(20), nullable=True)
